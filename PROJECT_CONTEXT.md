# Contexto del Proyecto

## Visión General
- **Nombre y descripción del proyecto**: SubNetx - Sistema de Gestión de VPN
- **Objetivos estratégicos**: Proporcionar una plataforma moderna y escalable para la gestión de redes VPN a través de microservicios
- **Público objetivo y stakeholders**: Administradores de redes, desarrolladores, y equipos de infraestructura que necesitan gestionar múltiples VPNs
- **Propuesta de valor única**: Gestión completa de VPNs basada en OpenVPN con una arquitectura de microservicios, ofreciendo interfaz web y API
- **Estado actual del proyecto**: En desarrollo activo
- **Roadmap estratégico**: Implementación de microservicios base (VPN, API, UI), expansión de funcionalidades y mejora de experiencia de usuario

## Arquitectura Técnica
- **Stack tecnológico detallado**:
  - **Backend**: Python 3.12, FastAPI, SQLAlchemy, Uvicorn
  - **Frontend**: Next.js 14, React 18, Material UI, TypeScript, Prisma ORM
  - **Base de datos**: PostgreSQL 16
  - **VPN**: OpenVPN, Easy-RSA
  - **Contenedores**: Docker, Docker Compose
  - **Monitoreo**: Supervisord, scripts personalizados (ping_monitor)
  - **Desarrollo**: ESLint, TypeScript, flake8, black, isort, mypy

- **Patrones arquitectónicos**: Arquitectura de microservicios, cada servicio con responsabilidad única, API RESTful
- **Diagramas de arquitectura**:
  - Tres servicios principales:
    - VPN Service: Gestión de OpenVPN, métricas y API específica para VPN (puerto 9020)
    - API Service: REST API para operaciones con la base de datos (puerto 8000)
    - UI Service: Interfaz de usuario web basada en Next.js (puerto 3200)
  - Base de datos PostgreSQL compartida
  - Red interna Docker para comunicación entre servicios

- **Decisiones técnicas clave**:
  - Uso de contenedores Docker para aislamiento y facilidad de despliegue
  - Microservicios para separación de responsabilidades
  - OpenVPN como tecnología VPN por su robustez y flexibilidad
  - FastAPI para API RESTful de alto rendimiento con documentación automática
  - Next.js para frontend moderno con SSR y optimización
  - Supervisord para gestión de múltiples procesos en el contenedor VPN
  - Prisma como ORM en el frontend para comunicación con BD

- **Consideraciones de escalabilidad**:
  - Arquitectura de microservicios permite escalar componentes individualmente
  - Containerización facilita la orquestación y gestión
  - Soporte para múltiples instancias VPN independientes a través de contenedores separados
  - Procesos independientes gestionados por Supervisord

- **Estrategias de seguridad**:
  - Contenedores con capacidades limitadas (NET_ADMIN solo para VPN)
  - Gestión segura de certificados y claves mediante volúmenes dedicados
  - Configuración de iptables para NAT y reenvío de paquetes
  - API con manejo estandarizado de errores y validación
  - Variables de entorno para configuración sensible

## Entorno de Desarrollo y Ejecución
- **Configuración del entorno de desarrollo**:
  - Basado en Docker Compose para desarrollo local
  - Hot reload para desarrollo rápido en todos los servicios
  - Volúmenes montados para persistencia de datos y desarrollo

- **Configuración de Docker/Contenedores**:
  - **Estructura y organización de contenedores**:
    - `subnetx_vpn`: Servicio principal de VPN basado en OpenVPN con Ubuntu 22.04
    - `subnetx_api`: API RESTful para gestión del sistema con Python 3.12
    - `subnetx_postgres`: Base de datos PostgreSQL 16
    - `subnetx_ui`: Frontend en Next.js 14 con Node 20
    - `subnetx_duckdns`: (Comentado en docker-compose) Servicio para actualización DNS dinámico

  - **Imágenes base utilizadas**:
    - VPN: Ubuntu 22.04 (instalación mínima con `--no-install-recommends`)
    - API: Python 3.12-slim
    - UI: Node 20-slim
    - DB: PostgreSQL 16-alpine

  - **Configuración de redes y volúmenes**:
    - Red bridge `subnetx` para comunicación entre servicios
    - Volúmenes para persistencia:
      - `./docker/volumes/certs:/etc/openvpn/certs` (Certificados VPN)
      - `./docker/volumes/logs:/var/log/openvpn` (Logs de OpenVPN)
      - `./docker/volumes/postgres:/var/lib/postgresql/data` (Datos PostgreSQL)
      - Volúmenes nombrados para node_modules y caché de Next.js

  - **Estrategia de orquestación**:
    - Docker Compose para desarrollo y despliegue simple
    - Supervisord para gestión de procesos internos en el contenedor VPN

  - **Entornos de desarrollo vs producción**:
    - Modo desarrollo con hot reload para API (uvicorn --reload)
    - Hot reload para UI (WATCHPACK_POLLING, CHOKIDAR_USEPOLLING)
    - Supervisord para monitoreo de procesos en VPN service
    - Configuración optimizada para desarrollo local

  - **IMPORTANTE: Todos los comandos deben ejecutarse dentro del contenedor correspondiente, no en el host**

  - **Estructura de Docker Compose y diagrama de servicios**:
    - VPN service: Gestión OpenVPN, métricas, API interna (puerto 9020)
    - API service: Endpoints REST para gestión (puerto 8000)
    - PostgreSQL: Base de datos compartida (puerto 5432)
    - UI service: Frontend Next.js (puerto 3200)
    - Dependencias configuradas para asegurar orden de inicio

  - **Estrategias de hot-reload y desarrollo interactivo con contenedores**:
    - API VPN y API principal: Uvicorn con flag `--reload`
    - UI: Next.js con WATCHPACK_POLLING y CHOKIDAR_USEPOLLING para detectar cambios en volúmenes montados
    - Scripts automatizados para setup inicial de BD (db:setup, db:push, db:init)

  - **Gestión de secretos y variables de entorno**:
    - Archivo `.env` en la raíz del proyecto para configuración global
    - Variables específicas para cada servicio en docker-compose.yaml
    - Soporte para DuckDNS (comentado, para gestión de IP dinámica)
    - Variables propagadas a los contenedores a través de Docker Compose

  - **Herramientas de debugging dentro de contenedores**:
    - Logs accesibles vía volúmenes montados
    - Utilidades de red (iputils, net-tools) instaladas en todos los servicios
    - Supervisord logs para cada proceso monitoreado
    - Herramientas para troubleshooting (lsof, procps) incluidas

  - **Estrategias de optimización de imágenes y capas**:
    - Limpieza de caché de apt en Dockerfiles
    - Uso de `--no-install-recommends` para reducir tamaño de imágenes
    - Instalación selectiva de dependencias
    - Capas optimizadas para mejorar eficiencia de caché

  - **Proceso de construcción y publicación de imágenes**:
    - Build context optimizado para cada servicio
    - Dockerfile específico para cada servicio
    - Configuraciones optimizadas para el propósito específico

  - **Mecanismos de comunicación entre contenedores**:
    - Red Docker dedicada (`subnetx`)
    - Comunicación vía nombres de host DNS internos (ej. subnetx_vpn, postgres)
    - Puertos específicos para cada servicio
    - Variables de entorno para configurar puntos de conexión

- **Dependencias del sistema**:
  - Docker Engine (versión 20+)
  - Docker Compose (versión 2+)
  - Git

- **Herramientas necesarias**:
  - Docker
  - Docker Compose
  - Git

- **Procedimientos de instalación**:
  1. Clonar repositorio: `git clone <repo_url>`
  2. Configurar archivo `.env` en la raíz con parámetros personalizados
  3. Ejecutar `docker-compose up -d` para iniciar todos los servicios
  4. Opcionalmente, acceder al contenedor VPN con `docker exec -it subnetx_vpn subnetx`

- **Verificación del entorno**:
  - API principal accesible en http://localhost:8000
  - VPN API accesible en http://localhost:9020
  - Base de datos PostgreSQL en puerto 5432
  - UI accesible en http://localhost:3200
  - Logs de servicios en ./docker/volumes/logs
  - Estado de procesos en contenedor VPN: `docker exec subnetx_vpn supervisorctl status`

## Estructura del Proyecto
- **Organización de directorios**:
  - `/services`: Contiene los servicios principales
    - `/services/vpn`: Servicio de VPN (OpenVPN)
      - `/scripts`: Scripts de gestión y API
      - `/config`: Configuraciones base para OpenVPN
    - `/services/api`: Servicio de API REST
      - `/src`: Código fuente de la API
    - `/services/ui`: Servicio de UI (frontend)
      - `/components`: Componentes React
      - `/pages`: Páginas Next.js
      - `/prisma`: Esquema y configuración Prisma
  - `/docker`: Configuraciones Docker
    - `/docker/supervisord.conf`: Configuración de supervisord para VPN
    - `/docker/volumes`: Volúmenes persistentes
  - `.env`: Variables de entorno del proyecto

- **Componentes principales**:
  - **VPN Service**:
    - Configuración y gestión de OpenVPN
    - Scripts para gestión de clientes VPN
    - API específica para VPN con routers para server y clients
    - Supervisord para gestión de procesos (api_server, vpn_api, ping_monitor)
    - Interfaz de terminal interactiva para gestión

  - **API Service**:
    - FastAPI para endpoints REST
    - Operaciones de base de datos dinámicas
    - Middleware CORS para integración frontend
    - Routers para operaciones específicas
    - Documentación automática Swagger/OpenAPI

  - **UI Service**:
    - Next.js 14 y React 18 para frontend
    - Material UI para componentes visuales
    - Prisma 6 para ORM y acceso a base de datos
    - Estructura completa TypeScript
    - Scripts automatizados para inicialización

  - **PostgreSQL**:
    - Almacenamiento persistente
    - Healthcheck para verificar disponibilidad

- **Flujos de datos**:
  - Frontend consume API REST principal y API VPN
  - API accede a base de datos PostgreSQL
  - VPN Service gestiona configuración OpenVPN y certificados
  - API VPN expone métricas y operaciones específicas de VPN
  - Métricas recolectadas por ping_monitor
  - Interconexión a través de red Docker interna

- **Integraciones externas**:
  - Integración configurada con DuckDNS para DNS dinámico (comentado)
  - Soporte para actualización automática de IP dinámica

- **APIs y endpoints**:
  - API principal en `/api/db/` para operaciones de base de datos (puerto 8000)
  - API VPN específica (puerto 9020) con endpoints para:
    - `/clients` - Gestión de clientes VPN
    - `/server` - Gestión del servidor VPN
  - API documentación en `/docs` (Swagger UI)

- **Servicios y microservicios**:
  - vpn: Gestión OpenVPN con API específica
  - api: Gestión general y base de datos
  - ui: Frontend Next.js (en desarrollo)
  - postgres: Base de datos

## Calidad y Estándares
- **Métricas de calidad de código**:
  - Herramientas de linting configuradas:
    - Python: flake8, black, isort, mypy, pylint
    - TypeScript/JavaScript: ESLint con config Next.js
  - Integración de formateo automático

- **Estándares de codificación**:
  - Python: PEP 8 (enforced by flake8, black)
  - TypeScript/JavaScript: ESLint con config Next.js
  - DocStrings estructurados
  - Tipado estático a través de TypeScript y type hints de Python

- **Prácticas de testing**:
  - Estructura preparada para pytest
  - Carpetas para tests en ambos servicios (vpn, api)
  - Jest configurado para testing de frontend

- **Cobertura de tests**:
  - En desarrollo, directorios de tests preparados

- **Procesos de revisión**:
  - No definidos explícitamente en el código actual

- **Herramientas de análisis estático**:
  - flake8, mypy, pylint para Python
  - ESLint, TypeScript para JavaScript/TypeScript

## Desarrollo y Despliegue
- **Flujo de trabajo de desarrollo**:
  - Desarrollo local con Docker Compose
  - Hot reload para cambios en tiempo real
  - Supervisord para monitoreo de procesos en VPN
  - Herramientas de desarrollo incluidas en contenedores

- **Estrategias de branching**:
  - No definidas explícitamente en el código actual

- **Procesos de CI/CD**:
  - No implementados aún

- **Entornos de despliegue**:
  - Local/desarrollo mediante Docker Compose
  - Soporte para múltiples instancias VPN independientes
  - Configuración modular para diferentes entornos

- **Estrategias de monitoreo**:
  - Logs de servicios montados en volúmenes para persistencia
  - Métricas personalizadas en VPN Service (ping_monitor)
  - Supervisord para control y reinicio automático de procesos
  - Healthchecks configurados para base de datos

- **Planes de rollback**:
  - No definidos explícitamente

## Seguridad
- **Análisis de riesgos**:
  - No documentado explícitamente

- **Medidas de seguridad implementadas**:
  - Contenedores con privilegios mínimos necesarios
  - NET_ADMIN solo para el servicio VPN
  - Gestión de certificados y claves mediante volúmenes dedicados
  - APIs con manejo estandarizado de errores y validación
  - Validación de entrada en todas las APIs
  - Middleware CORS configurado para API principal

- **Vulnerabilidades conocidas**:
  - No documentadas explícitamente

- **Prácticas de seguridad**:
  - Aislamiento de servicios mediante contenedores
  - Variables de entorno para configuración sensible
  - Validación de entradas en APIs
  - Control de acceso a recursos

- **Requisitos de cumplimiento**:
  - No documentados explícitamente

- **Planes de respuesta a incidentes**:
  - No documentados explícitamente

## Performance
- **Métricas de rendimiento**:
  - Monitoreo de ping implementado en VPN Service
  - Supervisord para reinicio automático de procesos fallidos
  - Healthchecks para verificar disponibilidad de servicios

- **Cuellos de botella identificados**:
  - No documentados explícitamente

- **Estrategias de optimización**:
  - Containerización para facilitar escalado horizontal
  - Supervisord para gestión de múltiples procesos
  - Optimización de imágenes Docker para reducir tamaño

- **Requisitos de escalabilidad**:
  - Arquitectura de microservicios facilita escalado independiente
  - Soporte para múltiples instancias VPN en contenedores separados
  - Configuración de recursos optimizada para cada servicio

- **Planes de capacidad**:
  - No documentados explícitamente

- **Monitoreo de performance**:
  - Scripts de métricas en VPN Service (ping_monitor)
  - Logs detallados de supervisord para cada proceso
  - Healthchecks para verificar estado de servicios

## Mantenimiento
- **Plan de mantenimiento**:
  - No documentado explícitamente

- **Frecuencia de actualizaciones**:
  - No documentada explícitamente

- **Procesos de soporte**:
  - Interfaz interactiva subnetx para gestión VPN
  - Documentación en README.md

- **Documentación de troubleshooting**:
  - README.md proporciona instrucciones básicas
  - Interfaz interactiva con ayuda incorporada
  - Logs centralizados en volúmenes accesibles

- **Procedimientos de backup**:
  - Volúmenes persistentes para datos importantes
  - Directorio de certificados mapeado para respaldo
  - Base de datos PostgreSQL en volumen dedicado

- **Planes de recuperación**:
  - No documentados explícitamente, pero la arquitectura permite reinicio de servicios independientes
  - Supervisord proporciona reinicio automático de procesos fallidos

## Troubleshooting y Resolución de Problemas

### Caso de Estudio: Error en la Creación de Clientes VPN

- **Problema Detectado**:
  - Error al intentar crear clientes VPN a través de la API
  - Mensajes de error indicando la falta del archivo `serial` en el directorio de Easy-RSA
  - Infraestructura PKI incompleta que impedía la generación de certificados para clientes

- **Causa Raíz**:
  - Secuencia de inicialización incorrecta: se intentaba crear clientes sin haber realizado previamente la configuración del servidor
  - Falta de validaciones en la API para verificar prerrequisitos antes de ejecutar operaciones
  - Ausencia de una infraestructura PKI completa (CA, certificados, archivo serial)

- **Proceso de Resolución**:
  1. **Análisis Sistemático**:
     - Inspección de logs y mensajes de error
     - Verificación de la estructura de directorios y archivos
     - Análisis del código en scripts relevantes

  2. **Limpieza del Entorno**:
     - Eliminación de certificados y archivos de configuración inconsistentes
     - Detención de procesos relacionados con OpenVPN
     - Reinicio de contenedores para asegurar un estado limpio

  3. **Aplicación de la Secuencia Correcta**:
     - Configuración inicial del servidor (setup) para generar la infraestructura PKI completa
     - Inicio del servidor VPN
     - Creación de clientes VPN

  4. **Verificación de la Solución**:
     - Pruebas completas de creación de múltiples clientes
     - Verificación de conectividad y configuración
     - Pruebas de detención y reinicio del servicio

  5. **Documentación de la Solución**:
     - Creación de documentación detallada sobre la secuencia correcta de operaciones
     - Registro de pasos específicos para resolver problemas similares

- **Mejoras Implementadas**:
  - **Verificaciones Adicionales**: Validación de prerrequisitos antes de intentar operaciones que dependen de configuración previa
  - **Mensajes de Error Mejorados**: Errores más descriptivos que indican la secuencia correcta
  - **Procedimiento Documentado**: Guía paso a paso para la configuración inicial y creación de clientes

- **Lecciones Aprendidas**:
  - La importancia de seguir la secuencia correcta: setup → start → client creation
  - Necesidad de validaciones más robustas en componentes interdependientes
  - Valor de mensajes de error descriptivos que indican acciones correctivas

- **Protocolo de Inicialización Recomendado**:
  ```bash
  # 1. Configuración inicial del servidor
  docker exec subnetx_vpn curl -X POST http://localhost:9020/server/setup -H "Content-Type: application/json" -d '{...}'

  # 2. Inicio del servidor VPN
  docker exec subnetx_vpn curl -X POST http://localhost:9020/server/start

  # 3. Creación de clientes
  docker exec subnetx_vpn curl -X POST http://localhost:9020/clients/ -H "Content-Type: application/json" -d '{...}'
  ```

- **Impacto de la Solución**:
  - Eliminación de errores en la creación de clientes VPN
  - Mejora en la robustez del sistema
  - Mayor claridad para los desarrolladores sobre las dependencias entre componentes
  - Base para futuras mejoras en la validación y gestión de errores
