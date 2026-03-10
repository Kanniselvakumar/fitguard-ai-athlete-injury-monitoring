from __future__ import annotations

from sqlalchemy import inspect, text

from app import db


def _add_column_if_missing(table_name: str, column_name: str, sql_definition: str) -> bool:
    inspector = inspect(db.engine)
    if not inspector.has_table(table_name):
        return False

    existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
    if column_name in existing_columns:
        return False

    db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_definition}"))
    db.session.commit()
    return True


def ensure_schema_compatibility() -> dict:
    """
    Applies minimal backward-compatible schema patches for legacy local databases.
    This is not a replacement for proper Alembic migrations, but prevents runtime 500s.
    """
    applied = []

    try:
        if _add_column_if_missing("athlete_profiles", "previous_injuries_count", "INT NOT NULL DEFAULT 0"):
            applied.append("athlete_profiles.previous_injuries_count")
    except Exception:
        db.session.rollback()

    return {"applied": applied}

