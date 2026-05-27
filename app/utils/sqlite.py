def ensure_sqlite() -> None:
    try:
        import sqlite3 as _sqlite3  # noqa: F401
    except Exception:
        try:
            import pysqlite3 as sqlite3  # type: ignore
            import sys as _sys
            _sys.modules['sqlite3'] = sqlite3
        except Exception:
            pass
