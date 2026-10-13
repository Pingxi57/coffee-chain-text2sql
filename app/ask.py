"""Core pipeline: question -> SQL -> result. Also runnable from the terminal."""
import re
import sys
from pathlib import Path

import pandas as pd

from llm import ask_llm
from schema_context import build_schema_text, get_connection

CONTEXT_DIR = Path(__file__).resolve().parent.parent / "context"

PROMPT_TEMPLATE = """You are an expert MySQL 8 analyst for a coffee-chain database.
Write ONE MySQL SELECT query (CTEs are allowed) that answers the question.
- Use only the tables, views and columns in the schema.
- Follow the business rules exactly.
- The question may be in Thai or English.
- Return only the SQL, with no explanation and no markdown.

Schema:
{schema}
{glossary}{examples}
Question: {question}
SQL:"""


def load_glossary() -> str:
    return (CONTEXT_DIR / "glossary.md").read_text(encoding="utf-8")


def load_examples() -> str:
    text = (CONTEXT_DIR / "examples.sql").read_text(encoding="utf-8")
    blocks = []
    for chunk in text.split("-- Question:")[1:]:
        question, _, sql = chunk.partition("\n")
        blocks.append(f"Question: {question.strip()}\nSQL:\n{sql.strip()}")
    return "\n\n".join(blocks)


GLOSSARY = load_glossary()
EXAMPLES = load_examples()


def clean_sql(text: str) -> str:
    # remove ```sql ... ``` fences if the model adds them
    text = re.sub(r"```(?:sql)?", "", text, flags=re.IGNORECASE)
    return text.strip().rstrip(";")


def load_schema() -> str:
    conn = get_connection()
    try:
        return build_schema_text(conn)
    finally:
        conn.close()


def build_prompt(question: str, schema: str, use_glossary=True, use_examples=True) -> str:
    glossary = f"\nBusiness rules:\n{GLOSSARY}\n" if use_glossary else ""
    examples = f"\nExamples:\n{EXAMPLES}\n" if use_examples else ""
    return PROMPT_TEMPLATE.format(
        schema=schema, glossary=glossary, examples=examples, question=question
    )


def generate_sql(question: str, schema: str, use_glossary=True, use_examples=True) -> str:
    prompt = build_prompt(question, schema, use_glossary, use_examples)
    return clean_sql(ask_llm(prompt))


def run_sql(sql: str, max_rows: int = 500) -> pd.DataFrame:
    conn = get_connection()
    try:
        cur = conn.cursor(buffered=True)
        cur.execute(sql)
        headers = [d[0] for d in cur.description]
        rows = cur.fetchmany(max_rows)
        cur.close()
    finally:
        conn.close()
    df = pd.DataFrame(rows, columns=headers)
    # MySQL DECIMAL comes back as text-like objects; make them real numbers
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError):
            pass
    return df


def main():
    question = " ".join(sys.argv[1:]) or "Which 5 branches had the highest revenue?"
    sql = generate_sql(question, load_schema())
    print("SQL:\n" + sql + "\n")
    print(run_sql(sql).head(20).to_string(index=False))


if __name__ == "__main__":
    main()
