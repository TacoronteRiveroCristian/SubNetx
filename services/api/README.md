# SubNetx API

A FastAPI-based backend for the SubNetx application.

## Project Overview

This project provides a RESTful API service that serves as the backend for the SubNetx application. It is built using FastAPI and follows a modular architecture for maintainability and scalability. It features a flexible database API that allows dynamic table creation and data manipulation.

## Folder Structure

```
.
├── src/                    # Source code directory
│   ├── api/                # API-related components
│   │   ├── dependencies/   # Dependency injection components
│   │   ├── models/         # Data models and schemas
│   │   └── routes/         # API route definitions
│   │       └── db_operations/  # Database operations API
│   │           ├── data.py     # CRUD operations for table data
│   │           ├── queries.py  # SQL query execution
│   │           └── tables.py   # Table management operations
│   ├── core/               # Core application components
│   │   └── database.py     # Database connection and session management
│   ├── services/           # Business logic services
│   ├── utils/              # Utility functions and helpers
│   └── main.py             # Main application entry point
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration
├── pyproject.toml          # Project configuration
└── .flake8                 # Flake8 configuration
```

## Getting Started

### Running the application

To run the application locally:

```bash
# Navigate to the project root
cd /path/to/project

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

The API will be available at http://localhost:8000

### API Documentation

Once the application is running, you can access the Swagger UI documentation at:
http://localhost:8000/docs

The API is organized in three main sections:

1. **Tables** - `/api/db/tables/*` - Endpoints for table management
2. **Data** - `/api/db/data/*` - Endpoints for data CRUD operations
3. **Queries** - `/api/db/queries/*` - Endpoints for custom SQL queries

### Database API Endpoints

#### Tables Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/db/tables/` | List all tables in the database |
| POST | `/api/db/tables/create` | Create a new table |
| GET | `/api/db/tables/{table_name}/schema` | Get schema of a specific table |
| DELETE | `/api/db/tables/{table_name}` | Delete a table |

#### Data Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/db/data/{table_name}` | Read data from a table with optional filtering |
| POST | `/api/db/data/{table_name}` | Insert data into a table |
| PUT | `/api/db/data/{table_name}` | Update data in a table |
| DELETE | `/api/db/data/{table_name}` | Delete data from a table |

#### Custom Queries

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/db/queries/raw` | Execute a raw SQL query |
| POST | `/api/db/queries/analyze` | Analyze a table (not implemented yet) |

### Environment Variables

- `DATABASE_URL` - Connection string for the database
- `API_HOST` - Host address for the API server (default: 0.0.0.0)
- `API_PORT` - Port for the API server (default: 8000)

## Changelog

- Fixed issue with duplicated API endpoints in Swagger UI by removing redundant tags
- Improved API organization with clear separation of tables, data, and queries endpoints
- Initial setup with FastAPI application structure
- Created basic folder structure
- Added main.py with root endpoint
