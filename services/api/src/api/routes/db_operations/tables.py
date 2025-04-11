from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from core.database import get_db
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, MetaData, Table, inspect, create_engine
import json

router = APIRouter()

@router.get("/")
async def list_tables(db: Session = Depends(get_db)):
    """
    List all tables in the database

    Returns:
        dict: A dictionary containing the list of tables

    Example:
        Response:
        ```json
        {
            "tables": ["users", "products", "orders"]
        }
        ```
    """
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.bind)
        tables = inspector.get_table_names()
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create")
async def create_table(
    table_config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Create a new table in the database based on provided schema

    Args:
        table_config: Configuration for the new table with schema

    Returns:
        dict: Result of table creation operation

    Example:
        Request body:
        ```json
        {
            "table_name": "employees",
            "columns": [
                {"name": "id", "type": "Integer", "primary_key": true},
                {"name": "name", "type": "String", "length": 100, "nullable": false},
                {"name": "email", "type": "String", "length": 200, "unique": true},
                {"name": "salary", "type": "Float"},
                {"name": "active", "type": "Boolean", "default": true},
                {"name": "notes", "type": "Text"}
            ]
        }
        ```
    """
    try:
        table_name = table_config.get("table_name")
        columns = table_config.get("columns", [])

        if not table_name:
            raise HTTPException(status_code=400, detail="Table name is required")

        if not columns:
            raise HTTPException(status_code=400, detail="At least one column is required")

        # Check if table already exists
        inspector = inspect(db.bind)
        if table_name in inspector.get_table_names():
            raise HTTPException(status_code=400, detail=f"Table '{table_name}' already exists")

        # Create table
        metadata = MetaData()
        sqlalchemy_columns = []

        # Map column types from request to SQLAlchemy types
        type_mapping = {
            "Integer": Integer,
            "String": String,
            "Float": Float,
            "Boolean": Boolean,
            "DateTime": DateTime,
            "Text": Text
        }

        for col in columns:
            col_name = col.get("name")
            col_type_name = col.get("type")

            if not col_name or not col_type_name:
                raise HTTPException(status_code=400, detail="Each column must have a name and type")

            # Get SQLAlchemy type
            col_type = type_mapping.get(col_type_name)
            if not col_type:
                raise HTTPException(status_code=400, detail=f"Unknown column type: {col_type_name}")

            # Handle String length
            if col_type_name == "String" and "length" in col:
                col_type = col_type(col.get("length", 255))

            # Create column with arguments
            kwargs = {}
            if col.get("primary_key"):
                kwargs["primary_key"] = True
            if col.get("nullable") is not None:
                kwargs["nullable"] = col.get("nullable")
            if col.get("unique"):
                kwargs["unique"] = True
            if "default" in col:
                kwargs["default"] = col.get("default")

            sqlalchemy_columns.append(Column(col_name, col_type, **kwargs))

        # Create table
        Table(table_name, metadata, *sqlalchemy_columns)
        metadata.create_all(db.bind)

        return {
            "status": "success",
            "message": f"Table '{table_name}' created successfully"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{table_name}/schema")
async def get_table_schema(table_name: str, db: Session = Depends(get_db)):
    """
    Get the schema of an existing table

    Args:
        table_name: Name of the table

    Returns:
        dict: Table schema information

    Example:
        Response:
        ```json
        {
            "table": "users",
            "schema": {
                "id": {"type": "integer", "primary_key": true},
                "name": {"type": "string", "nullable": false},
                "email": {"type": "string", "unique": true}
            }
        }
        ```
    """
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.bind)

        # Check if table exists
        if table_name not in inspector.get_table_names():
            raise HTTPException(status_code=404, detail=f"Table {table_name} does not exist")

        # Get column information
        columns = inspector.get_columns(table_name)
        primary_keys = inspector.get_pk_constraint(table_name)['constrained_columns']

        schema = {}
        for col in columns:
            col_type = str(col['type']).split('(')[0].lower()
            col_info = {
                "type": col_type,
                "nullable": col['nullable'],
                "primary_key": col['name'] in primary_keys
            }
            schema[col['name']] = col_info

        return {"table": table_name, "schema": schema}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{table_name}")
async def drop_table(table_name: str, db: Session = Depends(get_db)):
    """
    Drop an existing table from the database

    Args:
        table_name: Name of the table to drop

    Returns:
        dict: Result of the drop operation

    Example:
        Response:
        ```json
        {
            "status": "success",
            "message": "Table 'users' dropped successfully"
        }
        ```
    """
    try:
        inspector = inspect(db.bind)

        # Check if table exists
        if table_name not in inspector.get_table_names():
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' does not exist")

        # Create metadata and drop table
        metadata = MetaData()
        table = Table(table_name, metadata)

        # Get the table from metadata and drop it
        table.drop(db.bind)

        return {
            "status": "success",
            "message": f"Table '{table_name}' dropped successfully"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
