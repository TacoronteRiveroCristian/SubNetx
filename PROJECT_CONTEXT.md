# Contexto del Proyecto

## Visión General
- **Nombre y descripción del proyecto**: SubNetx - Sistema de Gestión de VPN
- **Objetivos estratégicos**: Proporcionar una plataforma moderna y escalable para la gestión de redes VPN a través de microservicios
- **Público objetivo y stakeholders**: Administradores de redes, desarrolladores, y equipos de infraestructura que necesitan gestionar múltiples VPNs
- **Propuesta de valor única**: Gestión completa de VPNs basada en OpenVPN con una arquitectura de microservicios, ofreciendo interfaz web y API
- **Estado actual del proyecto**: En desarrollo
- **Roadmap estratégico**: Implementación de microservicios base (VPN, API, UI), expansión de funcionalidades y mejora de experiencia de usuario

## Arquitectura Técnica
- **Stack tecnológico detallado**:
  - **Backend**: Python 3.12, FastAPI, SQLAlchemy
  - **Frontend**: Next.js, React, Material UI, TypeScript
  - **Base de datos**: PostgreSQL 16
  - **VPN**: OpenVPN, Easy-RSA
  - **Contenedores**: Docker, Docker Compose
  - **Monitoreo**: Herramientas de métricas personalizadas, ping_monitor

- **Patrones arquitectónicos**: Arquitectura de microservicios, cada servicio con responsabilidad única
- **Diagramas de arquitectura**:
  - Tres servicios principales:
    - VPN Service: Gestión de OpenVPN, métricas y API específica para VPN (puerto 9020)
    - API Service: REST API para operaciones con la base de datos (puerto 8000)
    - UI Service: Interfaz de usuario web basada en Next.js (puerto 3200, actualmente comentado)
  - Base de datos PostgreSQL compartida

- **Decisiones técnicas clave**:
  - Uso de contenedores Docker para aislamiento y facilidad de despliegue
  - Microservicios para separación de responsabilidades
  - OpenVPN como tecnología VPN por su robustez y flexibilidad
  - FastAPI para API RESTful de alto rendimiento
  - Next.js para frontend moderno con SSR
  - Supervisord para gestión de múltiples procesos en el contenedor VPN

- **Consideraciones de escalabilidad**:
  - Arquitectura de microservicios permite escalar componentes individualmente
  - Containerización facilita la orquestación y gestión
  - Soporte para múltiples instancias VPN independientes a través de contenedores separados

- **Estrategias de seguridad**:
  - Contenedores con capacidades limitadas (NET_ADMIN para VPN)
  - Gestión segura de certificados y claves
  - Configuración de iptables para NAT y reenvío de paquetes
  - API con manejo estandarizado de errores y validación

## Entorno de Desarrollo y Ejecución
- **Configuración del entorno de desarrollo**:
  - Basado en Docker Compose para desarrollo local
  - Hot reload para desarrollo rápido

- **Configuración de Docker/Contenedores**:
  - **Estructura y organización de contenedores**:
    - `subnetx_vpn`: Servicio principal de VPN basado en OpenVPN
    - `subnetx_api`: API RESTful para gestión del sistema
    - `subnetx_postgres`: Base de datos PostgreSQL
    - `subnetx_ui`: (Comentado en docker-compose) Frontend en Next.js
    - `subnetx_duckdns`: (Comentado en docker-compose) Servicio para actualización DNS dinámico

  - **Imágenes base utilizadas**:
    - VPN: Ubuntu 22.04
    - API: Python 3.12-slim
    - UI: Node 20-slim
    - DB: PostgreSQL 16

  - **Configuración de redes y volúmenes**:
    - Red bridge `subnetx` para comunicación entre servicios
    - Volúmenes para persistencia:
      - `./docker/volumes/certs:/etc/openvpn/certs`
      - `./docker/volumes/logs:/var/log/openvpn`
      - `./docker/volumes/postgres:/var/lib/postgresql/data`

  - **Estrategia de orquestación**: Docker Compose

  - **Entornos de desarrollo vs producción**:
    - Modo desarrollo con hot reload para API y UI
    - Supervisord para gestión de procesos en VPN service

  - **IMPORTANTE: Todos los comandos deben ejecutarse dentro del contenedor correspondiente, no en el host**

  - **Estructura de Docker Compose y diagrama de servicios**:
    - VPN service: Gestión OpenVPN, métricas, API interna (puerto 9020)
    - API service: Endpoints REST para gestión (puerto 8000)
    - PostgreSQL: Base de datos compartida (puerto 5432)
    - UI service: Frontend (comentado, pendiente implementación)

  - **Estrategias de hot-reload y desarrollo interactivo con contenedores**:
    - API: Uvicorn con flag `--reload`
    - UI: Next.js con WATCHPACK_POLLING y CHOKIDAR_USEPOLLING
    - VPN: Scripts de monitoreo con reinicio automático vía supervisord

  - **Gestión de secretos y variables de entorno**:
    - Archivo `.env` en la raíz del proyecto
    - Variables específicas en cada servicio
    - Soporte para DuckDNS (comentado, para IP dinámica)

  - **Herramientas de debugging dentro de contenedores**:
    - Logs accesibles vía volúmenes montados
    - Utilidades de red (iputils, net-tools) instaladas
    - Supervisord logs para cada proceso monitoreado

  - **Estrategias de optimización de imágenes y capas**:
    - Limpieza de caché de apt en Dockerfiles
    - Uso de `--no-install-recommends` para reducir tamaño
    - Instalación solo de dependencias necesarias

  - **Proceso de construcción y publicación de imágenes**:
    - Build context optimizado para cada servicio
    - Multi-stage build para optimizar tamaño final
    - Dockerfile específico para cada servicio

  - **Mecanismos de comunicación entre contenedores**:
    - Red Docker dedicada (`subnetx`)
    - Comunicación vía nombres de host DNS internos
    - Puertos específicos para cada servicio

- **Dependencias del sistema**:
  - Docker y Docker Compose
  - Git

- **Herramientas necesarias**:
  - Docker
  - Docker Compose
  - Git

- **Procedimientos de instalación**:
  1. Clonar repositorio
  2. Configurar archivo `.env` en la raíz
  3. Ejecutar `docker-compose up -d`
  4. Opcionalmente, acceder al contenedor VPN con `docker exec -it subnetx_vpn subnetx`

- **Verificación del entorno**:
  - API principal accesible en puerto configurado (default: 8000)
  - VPN API accesible en puerto configurado (default: 9020)
  - Base de datos PostgreSQL en puerto 5432
  - UI accesible en puerto configurado (en desarrollo)

## Estructura del Proyecto
- **Organización de directorios**:
  - `/services`: Contiene los servicios principales
    - `/services/vpn`: Servicio de VPN (OpenVPN)
    - `/services/api`: Servicio de API REST
    - `/services/ui`: Servicio de UI (frontend)
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
    - Operaciones de base de datos
    - Middleware CORS para integración frontend
    - Routers para operaciones específicas

  - **UI Service**:
    - Next.js y React para frontend
    - Material UI para componentes visuales
    - Prisma para ORM y acceso a base de datos
    - Estructura completa TypeScript

  - **PostgreSQL**:
    - Almacenamiento persistente
    - Healthcheck para verificar disponibilidad

- **Flujos de datos**:
  - Frontend consume API REST
  - API accede a base de datos PostgreSQL
  - VPN Service gestiona configuración OpenVPN
  - API VPN expone métricas y operaciones específicas de VPN
  - Métricas recolectadas por ping_monitor

- **Integraciones externas**:
  - Integración configurada con DuckDNS para DNS dinámico (comentado)

- **APIs y endpoints**:
  - API principal en `/api/db/` para operaciones de base de datos (puerto 8000)
  - API VPN específica (puerto 9020) con endpoints para:
    - `/clients` - Gestión de clientes VPN
    - `/server` - Gestión del servidor VPN

- **Servicios y microservicios**:
  - vpn: Gestión OpenVPN con API específica
  - api: Gestión general y base de datos
  - ui: Frontend Next.js (en desarrollo)
  - postgres: Base de datos

## Calidad y Estándares
- **Métricas de calidad de código**:
  - Herramientas de linting configuradas (flake8, black, isort, mypy)

- **Estándares de codificación**:
  - Python: PEP 8 (enforced by flake8, black)
  - TypeScript/JavaScript: ESLint con config Next.js

- **Prácticas de testing**:
  - Estructura preparada para pytest
  - Carpetas para tests en ambos servicios (vpn, api)

- **Cobertura de tests**:
  - En desarrollo, directorios de tests preparados

- **Procesos de revisión**:
  - No definidos explícitamente en el código actual

- **Herramientas de análisis estático**:
  - flake8, mypy para Python
  - ESLint, TypeScript para JavaScript/TypeScript

## Desarrollo y Despliegue
- **Flujo de trabajo de desarrollo**:
  - Desarrollo local con Docker Compose
  - Hot reload para cambios en tiempo real
  - Supervisord para monitoreo de procesos en VPN

- **Estrategias de branching**:
  - No definidas explícitamente en el código actual

- **Procesos de CI/CD**:
  - No implementados aún

- **Entornos de despliegue**:
  - Local/desarrollo mediante Docker Compose
  - Soporte para múltiples instancias VPN independientes

- **Estrategias de monitoreo**:
  - Logs de servicios
  - Métricas personalizadas en VPN Service (ping_monitor)
  - Supervisord para control de procesos

- **Planes de rollback**:
  - No definidos explícitamente

## Seguridad
- **Análisis de riesgos**:
  - No documentado explícitamente

- **Medidas de seguridad implementadas**:
  - Contenedores con privilegios mínimos necesarios
  - NET_ADMIN solo para el servicio VPN
  - Gestión de certificates y claves mediante volúmenes
  - APIs con manejo estandarizado de errores

- **Vulnerabilidades conocidas**:
  - No documentadas explícitamente

- **Prácticas de seguridad**:
  - Aislamiento de servicios mediante contenedores
  - Variables de entorno para configuración sensible
  - Validación de entradas en APIs

- **Requisitos de cumplimiento**:
  - No documentados explícitamente

- **Planes de respuesta a incidentes**:
  - No documentados explícitamente

## Performance
- **Métricas de rendimiento**:
  - Monitoreo de ping implementado en VPN Service
  - Supervisord para reinicio automático de procesos fallidos

- **Cuellos de botella identificados**:
  - No documentados explícitamente

- **Estrategias de optimización**:
  - Containerización para facilitar escalado horizontal
  - Supervisord para gestión de múltiples procesos

- **Requisitos de escalabilidad**:
  - Arquitectura de microservicios facilita escalado independiente
  - Soporte para múltiples instancias VPN en contenedores separados

- **Planes de capacidad**:
  - No documentados explícitamente

- **Monitoreo de performance**:
  - Scripts de métricas en VPN Service (ping_monitor)
  - Logs detallados de supervisord para cada proceso

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

- **Procedimientos de backup**:
  - Volúmenes persistentes para datos importantes
  - Directorio de certificados mapeado para respaldo

- **Planes de recuperación**:
  - No documentados explícitamente, pero la arquitectura permite reinicio de servicios independientes
