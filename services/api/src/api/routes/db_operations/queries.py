from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from core.database import get_db

router = APIRouter()

@router.post("/raw")
async def execute_raw_sql(
    sql: str = Body(..., description="Consulta SQL a ejecutar", embed=True),
    params: Optional[Dict[str, Any]] = Body({}, description="Parámetros para la consulta", embed=True),
    db: Session = Depends(get_db)
):
    """
    Execute raw SQL query with optional parameters

    Args:
        sql: SQL query string
        params: Query parameters

    Returns:
        dict: Query results

    Example:
        Request:
        POST /api/db/queries/raw
        ```json
        {
            "sql": "SELECT * FROM users WHERE id = :user_id",
            "params": {"user_id": 1}
        }
        ```

        Response:
        ```json
        {
            "results": [
                {"id": 1, "name": "John", "email": "john@example.com"}
            ],
            "count": 1
        }
        ```

    Warning:
        This endpoint should be used with caution and proper validation
        as it allows direct SQL execution.
    """
    try:
        from sqlalchemy import text

        # Execute SQL with parameters
        result = db.execute(text(sql), params)

        # Check if the query is a SELECT statement
        if sql.strip().upper().startswith("SELECT"):
            # Get all column names
            columns = result.keys()

            # Convert rows to dictionaries
            rows = [dict(zip(columns, row)) for row in result]

            return {
                "results": rows,
                "count": len(rows)
            }
        else:
            # For non-SELECT statements
            db.commit()
            return {
                "message": "Query executed successfully",
                "rows_affected": result.rowcount
            }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_table(
    table_name: str = Body(..., description="Nombre de la tabla a analizar", embed=True),
    db: Session = Depends(get_db)
):
    """
    Analyze a table to get statistics and information

    Args:
        table_name: Name of the table to analyze

    Returns:
        dict: Table statistics and information

    Example:
        Request:
        POST /api/db/queries/analyze
        ```json
        {
            "table_name": "users"
        }
        ```

        Response:
        ```json
        {
            "table_name": "users",
            "row_count": 100,
            "columns": [
                {"name": "id", "type": "integer", "nullable": false},
                {"name": "name", "type": "string", "nullable": false},
                {"name": "email", "type": "string", "nullable": false}
            ],
            "indexes": [
                {"name": "users_pkey", "columns": ["id"]}
            ]
        }
        ```
    """
    try:
        from sqlalchemy import inspect, text, Table, MetaData
        inspector = inspect(db.bind)

        # Check if table exists
        if table_name not in inspector.get_table_names():
            raise HTTPException(status_code=404, detail=f"Table {table_name} not found")

        # Get column information
        columns = inspector.get_columns(table_name)
        column_info = []
        for col in columns:
            column_info.append({
                "name": col['name'],
                "type": str(col['type']),
                "nullable": col['nullable']
            })

        # Get index information
        indexes = inspector.get_indexes(table_name)
        index_info = []
        for idx in indexes:
            index_info.append({
                "name": idx['name'],
                "columns": idx['column_names'],
                "unique": idx['unique']
            })

        # Get row count
        count_query = text(f"SELECT COUNT(*) FROM {table_name}")
        row_count = db.execute(count_query).scalar()

        return {
            "table_name": table_name,
            "row_count": row_count,
            "columns": column_info,
            "indexes": index_info
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
