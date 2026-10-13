"""Read the database schema and turn it into compact text for the LLM prompt."""
import os
from collections import defaultdict

import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


def _s(value):
    # information_schema sometimes comes back as bytes
    return value.decode() if isinstance(value, (bytes, bytearray)) else value


def build_schema_text(conn) -> str:
    db = os.getenv("DB_NAME")
    cur = conn.cursor()

    cur.execute(
        """
        SELECT c.TABLE_NAME, c.COLUMN_NAME, c.COLUMN_TYPE, c.COLUMN_KEY, t.TABLE_TYPE
        FROM information_schema.COLUMNS c
        JOIN information_schema.TABLES t
          ON t.TABLE_SCHEMA = c.TABLE_SCHEMA AND t.TABLE_NAME = c.TABLE_NAME
        WHERE c.TABLE_SCHEMA = %s
        ORDER BY t.TABLE_TYPE, c.TABLE_NAME, c.ORDINAL_POSITION
        """,
        (db,),
    )
    columns = defaultdict(list)
    kinds = {}
    for table, col, ctype, key, ttype in cur.fetchall():
        table, col, ctype = _s(table), _s(col), _s(ctype)
        pk = " PK" if _s(key) == "PRI" else ""
        columns[table].append(f"{col} {ctype}{pk}")
        kinds[table] = "VIEW" if _s(ttype) == "VIEW" else "TABLE"

    cur.execute(
        """
        SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY TABLE_NAME
        """,
        (db,),
    )
    fks = [f"{_s(t)}.{_s(c)} -> {_s(rt)}.{_s(rc)}" for t, c, rt, rc in cur.fetchall()]
    cur.close()

    lines = [f"{kinds[t]} {t}({', '.join(cols)})" for t, cols in columns.items()]
    lines.append("")
    lines.append("Foreign keys:")
    lines.extend(fks)
    return "\n".join(lines)


if __name__ == "__main__":
    conn = get_connection()
    print(build_schema_text(conn))
    conn.close()
