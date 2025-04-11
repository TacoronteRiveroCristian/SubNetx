from fastapi import APIRouter

# Import all routers
from .tables import router as tables_router
from .data import router as data_router
from .queries import router as queries_router

# Create main router
router = APIRouter()

# Include sub-routers with clear naming and separation of concerns
router.include_router(tables_router, prefix="/tables", tags=["tables"])  # Para gestión de tablas (crear, listar, modificar)
router.include_router(data_router, prefix="/data", tags=["data"])        # Para gestión de datos (CRUD)
router.include_router(queries_router, prefix="/queries", tags=["queries"]) # Para consultas personalizadas
