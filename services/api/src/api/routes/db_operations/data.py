from fastapi import APIRouter, Depends, HTTPException, Body, Query
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import Table, Column, MetaData, select, insert, update, delete
from core.database import get_db
import json

router = APIRouter()

@router.get("/{table_name}")
async def read_data(
    table_name: str,
    db: Session = Depends(get_db),
    limit: int = Query(100, description="Número máximo de registros a retornar"),
    offset: int = Query(0, description="Desplazamiento para paginación"),
    order_by: Optional[str] = Query(None, description="Campo para ordenar")
):
    """
    Read data from a table with optional filtering and pagination

    Args:
        table_name: Name of the table to query
        limit: Maximum number of records to return
        offset: Offset for pagination
        order_by: Field to order by

    Returns:
        dict: Records from the table

    Example:
        Request:
        GET /api/db/data/users?limit=10&offset=0&order_by=id

        Response:
        ```json
        {
            "data": [
                {"id": 1, "name": "John", "email": "john@example.com"},
                {"id": 2, "name": "Jane", "email": "jane@example.com"}
            ],
            "total": 2,
            "limit": 10,
            "offset": 0
        }
        ```
    """
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.bind)

        # Check if table exists
        if table_name not in inspector.get_table_names():
            raise HTTPException(status_code=404, detail=f"Table {table_name} not found")

        # Get table object dynamically
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=db.bind)

        # Build query
        query = select(table)

        # Apply ordering if specified
        if order_by and order_by in table.columns:
            query = query.order_by(table.columns[order_by])

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = db.execute(query)

        # Get column names
        columns = [column.name for column in table.columns]

        # Convert to list of dictionaries
        data = [dict(zip(columns, row)) for row in result]

        # Get total count
        count_query = select(table)
        total = len(db.execute(count_query).all())

        return {
            "data": data,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{table_name}")
async def create_data(
    table_name: str,
    data: Dict[str, Any] = Body(..., description="Los datos a insertar en la tabla"),
    db: Session = Depends(get_db)
):
    """
    Insert data into a table

    Args:
        table_name: Name of the target table
        data: Data to insert (keys should match column names)

    Returns:
        dict: Result of the operation

    Example:
        Request:
        POST /api/db/data/users
        ```json
        {
            "name": "John",
            "email": "john@example.com"
        }
        ```

        Response:
        ```json
        {
            "message": "Data inserted successfully",
            "row_count": 1
        }
        ```
    """
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.bind)

        # Check if table exists
        if table_name not in inspector.get_table_names():
            raise HTTPException(status_code=404, detail=f"Table {table_name} not found")

        # Get table object dynamically
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=db.bind)

        # Validate data against table columns
        valid_columns = {column.name for column in table.columns}
        for key in data.keys():
            if key not in valid_columns:
                raise HTTPException(status_code=400, detail=f"Column '{key}' does not exist in table '{table_name}'")

        # Insert data
        query = insert(table).values(**data)
        result = db.execute(query)
        db.commit()

        return {
            "message": "Data inserted successfully",
            "row_count": result.rowcount
        }
    except HTTPException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{table_name}")
async def update_data(
    table_name: str,
    data: Dict[str, Any] = Body(..., description="Los datos a actualizar"),
    where: Dict[str, Any] = Body(..., description="Condiciones para la actualización"),
    db: Session = Depends(get_db)
):
    """
    Update data in a table

    Args:
        table_name: Name of the target table
        data: Data to update (keys should match column names)
        where: Conditions for the update (keys should match column names)

    Returns:
        dict: Result of the operation

    Example:
        Request:
        PUT /api/db/data/users
        ```json
        {
            "data": {
                "name": "Updated Name"
            },
            "where": {
                "id": 1
            }
        }
        ```

        Response:
        ```json
        {
            "message": "Data updated successfully",
            "rows_affected": 1
        }
        ```
    """
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.bind)

        # Check if table exists
        if table_name not in inspector.get_table_names():
            raise HTTPException(status_code=404, detail=f"Table {table_name} not found")

        # Get table object dynamically
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=db.bind)

        # Validate data against table columns
        valid_columns = {column.name for column in table.columns}
        for key in data.keys():
            if key not in valid_columns:
                raise HTTPException(status_code=400, detail=f"Column '{key}' does not exist in table '{table_name}'")

        for key in where.keys():
            if key not in valid_columns:
                raise HTTPException(status_code=400, detail=f"Column '{key}' does not exist in table '{table_name}'")

        # Build update query
        query = update(table).values(**data)

        # Add where conditions
        for key, value in where.items():
            query = query.where(table.columns[key] == value)

        # Execute query
        result = db.execute(query)
        db.commit()

        return {
            "message": "Data updated successfully",
            "rows_affected": result.rowcount
        }
    except HTTPException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{table_name}")
async def delete_data(
    table_name: str,
    where: Dict[str, Any] = Body(..., description="Condiciones para eliminar registros"),
    db: Session = Depends(get_db)
):
    """
    Delete data from a table

    Args:
        table_name: Name of the target table
        where: Conditions for deletion (keys should match column names)

    Returns:
        dict: Result of the operation

    Example:
        Request:
        DELETE /api/db/data/users
        ```json
        {
            "id": 1
        }
        ```

        Response:
        ```json
        {
            "message": "Data deleted successfully",
            "rows_affected": 1
        }
        ```
    """
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.bind)

        # Check if table exists
        if table_name not in inspector.get_table_names():
            raise HTTPException(status_code=404, detail=f"Table {table_name} not found")

        # Get table object dynamically
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=db.bind)

        # Validate where conditions against table columns
        valid_columns = {column.name for column in table.columns}
        for key in where.keys():
            if key not in valid_columns:
                raise HTTPException(status_code=400, detail=f"Column '{key}' does not exist in table '{table_name}'")

        # Build delete query
        query = delete(table)

        # Add where conditions
        for key, value in where.items():
            query = query.where(table.columns[key] == value)

        # Execute query
        result = db.execute(query)
        db.commit()

        return {
            "message": "Data deleted successfully",
            "rows_affected": result.rowcount
        }
    except HTTPException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
