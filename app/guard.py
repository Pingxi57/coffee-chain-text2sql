"""Safety checks that every generated query must pass before it reaches MySQL."""
import sqlglot
from sqlglot import exp

MAX_ROWS = 500

_BLOCKED_NODES = tuple(
    getattr(exp, name)
    for name in ["Insert", "Update", "Delete", "Drop", "Create", "Alter",
                 "Merge", "TruncateTable", "Command"]
    if hasattr(exp, name)
)
_BLOCKED_FUNCTIONS = {"SLEEP", "BENCHMARK", "LOAD_FILE", "GET_LOCK"}


class UnsafeSQLError(ValueError):
    """Raised when generated SQL is not a single, read-only SELECT."""


def check_sql(sql: str) -> str:
    """Return a safe version of the SQL, or raise UnsafeSQLError."""
    try:
        statements = [s for s in sqlglot.parse(sql, read="mysql") if s is not None]
    except sqlglot.errors.ParseError as e:
        raise UnsafeSQLError(f"Could not parse the SQL: {e}") from e

    if len(statements) != 1:
        raise UnsafeSQLError("Only one SQL statement is allowed.")
    tree = statements[0]

    if not isinstance(tree, exp.Query):
        raise UnsafeSQLError("Only SELECT queries are allowed.")
    if tree.find(*_BLOCKED_NODES):
        raise UnsafeSQLError("The query contains a statement that changes data.")
    for func in tree.find_all(exp.Anonymous):
        if func.name.upper() in _BLOCKED_FUNCTIONS:
            raise UnsafeSQLError(f"The function {func.name.upper()}() is not allowed.")

    # Add a row limit when the model forgot one
    if isinstance(tree, exp.Select) and not tree.args.get("limit"):
        return f"{sql}\nLIMIT {MAX_ROWS}"
    return sql
