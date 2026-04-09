import os
import re
import io
import pandas as pd
from sqlalchemy import create_engine, text

def init_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", echo=False)

def import_csv(engine, uploaded_file):
    df = pd.read_csv(io.BytesIO(uploaded_file.read())).fillna(0)
    table = re.sub(r"\W+", "_", uploaded_file.name.split(".")[0]).lower()
    df.to_sql(table, engine, if_exists="replace", index=False)
    return table

def list_tables(engine):
    with engine.connect() as conn:
        res = conn.execute(text("SELECT name FROM sqlite_schema WHERE type='table'"))
        return [r[0] for r in res.fetchall()]

def get_schema_description(engine):
    with engine.connect() as conn:
        tables = conn.execute(
            text("SELECT name FROM sqlite_schema WHERE type='table'")
        ).fetchall()

        schema_lines = []
        for (table,) in tables:
            cols = conn.execute(
                text(f"PRAGMA table_info({table})")
            ).fetchall()
            col_names = [c[1] for c in cols]

            schema_lines.append(
                f"Table '{table}' has columns: {', '.join(col_names)}"
            )

        return "\n".join(schema_lines)
