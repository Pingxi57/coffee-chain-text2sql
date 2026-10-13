import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from guard import MAX_ROWS, UnsafeSQLError, check_sql  # noqa: E402


def test_allows_simple_select():
    assert check_sql("SELECT COUNT(*) FROM Orders LIMIT 1") == "SELECT COUNT(*) FROM Orders LIMIT 1"


def test_allows_cte():
    sql = "WITH t AS (SELECT Branch_ID FROM Branch) SELECT * FROM t LIMIT 5"
    assert check_sql(sql) == sql


def test_adds_limit_when_missing():
    assert check_sql("SELECT * FROM Product").endswith(f"LIMIT {MAX_ROWS}")


@pytest.mark.parametrize("sql", [
    "DELETE FROM Orders",
    "UPDATE Member SET Points = 0",
    "DROP TABLE Orders",
    "INSERT INTO Branch (Branch_Name) VALUES ('x')",
    "SELECT 1; DROP TABLE Orders",
    "SELECT SLEEP(10)",
])
def test_blocks_unsafe_sql(sql):
    with pytest.raises(UnsafeSQLError):
        check_sql(sql)
