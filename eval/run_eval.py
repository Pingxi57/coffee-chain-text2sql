"""Measure text-to-SQL accuracy against the gold question set.

Usage:
  python eval/run_eval.py --check-gold        # run the gold SQL only (no LLM calls)
  python eval/run_eval.py --config full       # evaluate one prompt configuration
  python eval/run_eval.py --config all        # evaluate all four configurations
  python eval/run_eval.py --summary           # rebuild the results table only

Results are appended to eval/results.csv, so a run that stops (e.g. quota reached)
continues from where it left off next time.
"""
import argparse
import csv
import math
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
from ask import generate_sql, load_schema, run_sql  # noqa: E402

QUESTIONS_FILE = ROOT / "eval" / "questions.sql"
RESULTS_FILE = ROOT / "eval" / "results.csv"
SUMMARY_FILE = ROOT / "eval" / "results.md"
LEVELS = ["easy", "medium", "hard"]
CONFIGS = {
    "schema_only": dict(use_glossary=False, use_examples=False),
    "glossary": dict(use_glossary=True, use_examples=False),
    "examples": dict(use_glossary=False, use_examples=True),
    "full": dict(use_glossary=True, use_examples=True),
    "full_v2": dict(use_glossary=True, use_examples=True, checks=True),
}
FIELDS = ["config", "qid", "level", "question", "correct", "error", "generated_sql"]


def load_questions():
    text = QUESTIONS_FILE.read_text(encoding="utf-8")
    items = []
    for chunk in text.split("\n-- Q")[1:]:
        header, _, sql = chunk.partition("\n")
        qid, level, question = [part.strip() for part in header.split("|", 2)]
        items.append({"qid": f"Q{qid}", "level": level, "question": question, "sql": sql.strip()})
    return items


def _norm(value):
    if value is None:
        return "NULL"
    try:
        return f"{round(float(value), 1):.1f}"
    except (TypeError, ValueError):
        return str(value).strip().lower()


def _is_num(value):
    try:
        float(value)
        return value is not None
    except (TypeError, ValueError):
        return False


def _col_match(gold_vals, pred_vals):
    """Numbers match within a small tolerance; text matches exactly (case-insensitive)."""
    if all(_is_num(v) for v in gold_vals) and all(_is_num(v) for v in pred_vals):
        g = sorted(float(v) for v in gold_vals)
        p = sorted(float(v) for v in pred_vals)
        return all(math.isclose(a, b, rel_tol=1e-3, abs_tol=0.051) for a, b in zip(g, p))
    return Counter(_norm(v) for v in gold_vals) == Counter(_norm(v) for v in pred_vals)


def results_match(gold_df, pred_df):
    """Same row count, and every gold column appears in the prediction."""
    if len(gold_df) != len(pred_df):
        return False
    pred_cols = [list(pred_df.iloc[:, i]) for i in range(pred_df.shape[1])]
    return all(
        any(_col_match(list(gold_df.iloc[:, i]), pc) for pc in pred_cols)
        for i in range(gold_df.shape[1])
    )


def check_gold(questions):
    all_ok = True
    for q in questions:
        try:
            df = run_sql(q["sql"])
            print(f"{q['qid']}  OK   {len(df):>4} rows   {q['question']}")
            if len(df) == 0 or (df.size == 1 and _norm(df.iat[0, 0]) in ("0.0", "NULL")):
                print("       ! empty or zero result - check this question")
        except Exception as e:
            all_ok = False
            print(f"{q['qid']}  FAIL {e}")
    return all_ok


def load_done():
    if not RESULTS_FILE.exists():
        return set()
    with RESULTS_FILE.open(encoding="utf-8") as f:
        return {(r["config"], r["qid"]) for r in csv.DictReader(f)}


class DailyQuotaError(Exception):
    """The daily free quota is used up; stop and continue another day."""


def generate_with_retry(question, schema, cfg, waits=(65, 65, 65)):
    """Wait and retry on per-minute rate limits; raise DailyQuotaError on the daily limit."""
    for wait in (*waits, None):
        try:
            return generate_sql(question, schema, **cfg)
        except Exception as e:
            msg = str(e)
            if "429" not in msg and "RESOURCE_EXHAUSTED" not in msg:
                raise
            if "PerDay" in msg or wait is None:
                raise DailyQuotaError(msg) from e
            print(f"   rate limit hit, waiting {wait}s...")
            time.sleep(wait)


def run(config_names, questions, delay):
    schemas = {False: load_schema(), True: load_schema(include_checks=True)}
    done = load_done()
    new_file = not RESULTS_FILE.exists()
    with RESULTS_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        for name in config_names:
            for q in questions:
                if (name, q["qid"]) in done:
                    continue
                row = {"config": name, "qid": q["qid"], "level": q["level"],
                       "question": q["question"], "correct": 0, "error": "", "generated_sql": ""}
                try:
                    cfg = dict(CONFIGS[name])
                    checks = cfg.pop("checks", False)
                    sql = generate_with_retry(q["question"], schemas[checks], cfg)
                    row["generated_sql"] = sql
                    row["correct"] = int(results_match(run_sql(q["sql"]), run_sql(sql)))
                except Exception as e:
                    msg = str(e)
                    if isinstance(e, DailyQuotaError):
                        print("Daily quota reached - stopping. Run the same command tomorrow to continue.")
                        return
                    row["error"] = msg[:300]
                writer.writerow(row)
                f.flush()
                print(f"[{name}] {q['qid']} {'PASS' if row['correct'] else 'FAIL'}")
                time.sleep(delay)


def rescore():
    """Re-check every stored prediction against the current gold SQL (no LLM calls)."""
    with RESULTS_FILE.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    gold = {q["qid"]: q["sql"] for q in load_questions()}
    gold_results = {}
    for r in rows:
        if not r["generated_sql"]:
            continue
        try:
            if r["qid"] not in gold_results:
                gold_results[r["qid"]] = run_sql(gold[r["qid"]])
            r["correct"] = str(int(results_match(gold_results[r["qid"]], run_sql(r["generated_sql"]))))
        except Exception:
            r["correct"] = "0"
    with RESULTS_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def summarize():
    with RESULTS_FILE.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    def pct(subset):
        if not subset:
            return "-"
        ok = sum(int(r["correct"]) for r in subset)
        return f"{100 * ok / len(subset):.0f}% ({ok}/{len(subset)})"

    lines = ["| Configuration | Easy | Medium | Hard | Overall |", "|---|---|---|---|---|"]
    for name in CONFIGS:
        r = [x for x in rows if x["config"] == name]
        if r:
            cells = [pct([x for x in r if x["level"] == lv]) for lv in LEVELS]
            lines.append(f"| {name} | {' | '.join(cells)} | {pct(r)} |")
    table = "\n".join(lines)
    SUMMARY_FILE.write_text("# Evaluation results\n\n" + table + "\n", encoding="utf-8")
    print(table)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-gold", action="store_true")
    parser.add_argument("--config", default="full", choices=[*CONFIGS, "all"])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--delay", type=float, default=10.0, help="seconds between LLM calls")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--rescore", action="store_true", help="re-check stored predictions")
    args = parser.parse_args()

    questions = load_questions()
    if args.limit:
        questions = questions[: args.limit]
    if args.check_gold:
        sys.exit(0 if check_gold(questions) else 1)
    if args.rescore:
        rescore()
        summarize()
        return
    if not args.summary:
        run(list(CONFIGS) if args.config == "all" else [args.config], questions, args.delay)
    if RESULTS_FILE.exists():
        summarize()


if __name__ == "__main__":
    main()
