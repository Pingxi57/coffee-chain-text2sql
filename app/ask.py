"""Prototype: question -> SQL -> result, in the terminal."""
import re
import sys

from llm import ask_llm
from schema_context import build_schema_text, get_connection

PROMPT_TEMPLATE = """You are an expert MySQL 8 analyst for a coffee-chain database.
Write ONE MySQL SELECT query that answers the question.
Use only the tables, views and columns in the schema below.
The question may be in Thai or English.
Return only the SQL, with no explanation.

Schema:
{schema}

Question: {question}
SQL:"""


def clean_sql(text: str) -> str:
    # remove ```sql ... ``` fences if the model adds them
    text = re.sub(r"```(?:sql)?", "", text, flags=re.IGNORECASE)
    return text.strip().rstrip(";")


def main():
    question = " ".join(sys.argv[1:]) or "Which 5 branches had the highest revenue?"
    conn = get_connection()
    schema = build_schema_text(conn)

    sql = clean_sql(ask_llm(PROMPT_TEMPLATE.format(schema=schema, question=question)))
    print("SQL:\n" + sql + "\n")

    cur = conn.cursor()
    cur.execute(sql)
    headers = [d[0] for d in cur.description]
    print(" | ".join(headers))
    for row in cur.fetchmany(20):
        print(" | ".join(str(v) for v in row))
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
