# Operaciones de Base de Datos API

Este módulo proporciona una API flexible para trabajar con bases de datos de forma dinámica. Permite crear tablas, gestionar datos y ejecutar consultas sin necesidad de definir modelos fijos.

## Estructura del Módulo

El módulo se divide en tres secciones principales, cada una con su propio conjunto de endpoints:

1. **Tables (`/api/db/tables`)**: Gestión de tablas (crear, listar, obtener esquema, eliminar)
2. **Data (`/api/db/data`)**: Operaciones CRUD para los datos dentro de las tablas
3. **Queries (`/api/db/queries`)**: Ejecución de consultas SQL personalizadas

## Cómo Usar

### 1. Gestión de Tablas

#### Crear una tabla
```
POST /api/db/tables/create
```

Ejemplo de solicitud:
```json
{
    "table_name": "empleados",
    "columns": [
        {"name": "id", "type": "Integer", "primary_key": true},
        {"name": "nombre", "type": "String", "length": 100, "nullable": false},
        {"name": "email", "type": "String", "length": 200, "unique": true},
        {"name": "salario", "type": "Float"},
        {"name": "activo", "type": "Boolean", "default": true},
        {"name": "notas", "type": "Text"}
    ]
}
```

#### Listar todas las tablas
```
GET /api/db/tables
```

#### Ver esquema de una tabla
```
GET /api/db/tables/{nombre_tabla}/schema
```

#### Eliminar una tabla
```
DELETE /api/db/tables/{nombre_tabla}
```

### 2. Gestión de Datos

#### Consultar datos
```
GET /api/db/data/{nombre_tabla}?limit=100&offset=0&order_by=id
```

#### Insertar datos
```
POST /api/db/data/{nombre_tabla}
```
Ejemplo:
```json
{
    "nombre": "Juan Pérez",
    "email": "juan@ejemplo.com",
    "salario": 35000,
    "activo": true
}
```

#### Actualizar datos
```
PUT /api/db/data/{nombre_tabla}
```
Ejemplo:
```json
{
    "data": {
        "salario": 40000
    },
    "where": {
        "id": 1
    }
}
```

#### Eliminar datos
```
DELETE /api/db/data/{nombre_tabla}
```
Ejemplo:
```json
{
    "where": {
        "id": 1
    }
}
```

### 3. Consultas Personalizadas

#### Ejecutar consulta SQL
```
POST /api/db/queries/execute
```
Ejemplo:
```json
{
    "query": "SELECT * FROM empleados WHERE salario > :min_salario",
    "params": {
        "min_salario": 30000
    }
}
```

## Flujo de Trabajo Típico

1. Crear una tabla usando el endpoint `/api/db/tables/create`
2. Insertar datos usando `/api/db/data/{nombre_tabla}` (POST)
3. Consultar los datos usando `/api/db/data/{nombre_tabla}` (GET)
4. Realizar consultas más complejas usando `/api/db/queries/execute`
