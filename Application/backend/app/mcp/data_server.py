import os
import sqlite3
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Get the database path - you can adjust this as needed
DB_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "nba_stats.db"
)


class QueryRequest(BaseModel):
    query: str
    params: Optional[List[Any]] = None


class TableInfo(BaseModel):
    table_name: str
    columns: List[str]


def get_db_connection():
    return sqlite3.connect(DB_FILE)


@app.get("/tables")
async def get_tables() -> List[TableInfo]:
    """Get a list of tables and their columns in the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        result = []
        for (table_name,) in tables:
            # Get column info for each table
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            result.append(TableInfo(table_name=table_name, columns=columns))

        return result
    finally:
        conn.close()


@app.post("/query")
async def execute_query(request: QueryRequest) -> Dict[str, Any]:
    """Execute a SQL query and return the results."""
    if not request.query.lower().strip().startswith(("select", "with")):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        params = request.params or []
        cursor.execute(request.query, params)

        # Get column names
        columns = [desc[0] for desc in cursor.description]
        # Fetch all rows
        rows = cursor.fetchall()

        return {"columns": columns, "rows": rows, "rowCount": len(rows)}
    except sqlite3.Error as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@app.get("/schema")
async def get_schema() -> Dict[str, Any]:
    """Get the complete database schema."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        schema = {}
        for (table_name,) in tables:
            # Get detailed table info including columns, types, constraints
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            # Format column info
            schema[table_name] = [
                {
                    "name": col[1],
                    "type": col[2],
                    "notnull": bool(col[3]),
                    "default": col[4],
                    "pk": bool(col[5]),
                }
                for col in columns
            ]

            # Get foreign key info
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = cursor.fetchall()
            if foreign_keys:
                schema[table_name].append(
                    {
                        "foreign_keys": [
                            {"table": fk[2], "from": fk[3], "to": fk[4]}
                            for fk in foreign_keys
                        ]
                    }
                )

        return schema
    finally:
        conn.close()
