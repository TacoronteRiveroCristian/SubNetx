# Tarea Principal: Iniciar y Verificar el Servicio VPN con la API en Puerto 9000

## Enfoque de Innovación
- Implementación de una solución de verificación dinámica de servicios containerizados mediante comprobación automática de endpoints y variables de entorno
- Aplicación de técnicas de modificación de configuración en tiempo real con reinicio selectivo de servicios
- Evaluación comparativa de rendimiento de API antes y después de cambios de configuración
- Sistema de rollback automatizado en caso de fallos de comunicación

## Subtareas

1. [x] Verificar entorno de Docker y configuración
   - Descripción: Comprobar que Docker y Docker Compose están correctamente instalados y configurados
   - Dependencias: Ninguna
   - Recursos: Docker, Docker Compose
   - Componente innovador: Análisis de estado del entorno con validación cruzada
   - Entorno de Ejecución: Host (no contenedor)
   - Verificación: Docker y Docker Compose responden correctamente a comandos básicos

2. [x] Inspeccionar configuración de entorno (.env)
   - Descripción: Validar que el archivo .env tiene las variables necesarias para la API VPN
   - Dependencias: Subtarea 1
   - Recursos: .env, configuración de entorno
   - Verificación: Archivo .env contiene VPN_API_PORT=9000 y VPN_API_HOST=0.0.0.0
   - Entorno de Ejecución: Host (no contenedor)

3. [x] Revisar configuración de supervisord para VPN API
   - Descripción: Verificar que la configuración de supervisord está correctamente configurada para iniciar la API VPN
   - Dependencias: Subtarea 2
   - Recursos: docker/supervisord.conf
   - Verificación: El programa vpn_api está correctamente configurado en el archivo supervisord.conf
   - Entorno de Ejecución: Host (no contenedor)

4. [x] Revisar docker-compose.yaml para verificar mapeo de puertos
   - Descripción: Comprobar que el puerto de la API VPN está correctamente mapeado en el archivo docker-compose.yaml
   - Dependencias: Subtarea 2
   - Recursos: docker-compose.yaml
   - Verificación: El servicio subnetx mapea correctamente ${VPN_API_PORT}:${VPN_API_PORT}
   - Entorno de Ejecución: Host (no contenedor)

5. [x] Detener servicios existentes
   - Descripción: Detener cualquier servicio Docker en ejecución relacionado con SubNetx
   - Dependencias: Subtarea 1
   - Recursos: Docker Compose
   - Verificación: Todos los contenedores de SubNetx están detenidos
   - Entorno de Ejecución: Host (no contenedor)

6. [x] Construir e iniciar solo el servicio VPN y la base de datos
   - Descripción: Construir e iniciar únicamente los servicios necesarios (subnetx y postgres)
   - Dependencias: Subtarea 5
   - Recursos: Docker Compose
   - Verificación: Los contenedores subnetx_vpn y subnetx_postgres están en ejecución
   - Entorno de Ejecución: Host (no contenedor)
   - Impacto Disruptivo: Medio

7. [x] Verificar que la base de datos está operativa
   - Descripción: Comprobar que el servicio PostgreSQL está correctamente iniciado y operativo
   - Dependencias: Subtarea 6
   - Recursos: Docker, PostgreSQL
   - Verificación: El healthcheck de PostgreSQL devuelve un estado saludable
   - Entorno de Ejecución: Host y contenedor postgres

8. [x] Verificar que la API VPN está en ejecución
   - Descripción: Comprobar que la API VPN se ha iniciado correctamente dentro del contenedor
   - Dependencias: Subtarea 6
   - Recursos: Docker, curl
   - Verificación: El proceso de la API VPN está en ejecución dentro del contenedor subnetx_vpn
   - Entorno de Ejecución: Contenedor subnetx_vpn
   - Servicio Docker: subnetx

9. [x] Comprobar accesibilidad de la API VPN en puerto 9000
   - Descripción: Verificar que la API VPN es accesible desde el host en el puerto 9000
   - Dependencias: Subtarea 8
   - Recursos: curl, navegador web
   - Verificación: Se obtiene respuesta HTTP 200 OK al acceder a http://localhost:9000
   - Entorno de Ejecución: Host (no contenedor)
   - Impacto Disruptivo: Bajo

10. [x] Verificar la funcionalidad de la API VPN
    - Descripción: Comprobar que la API responde correctamente a las solicitudes
    - Dependencias: Subtarea 9
    - Recursos: curl, navegador web
    - Verificación: La API responde con un mensaje de éxito y la versión correcta
    - Entorno de Ejecución: Host (no contenedor)

11. [x] Modificar el puerto de la API VPN en el archivo .env
    - Descripción: Cambiar el puerto de la API VPN de 9000 a 9001 en el archivo .env
    - Dependencias: Subtarea 10
    - Recursos: .env
    - Verificación: El archivo .env contiene ahora VPN_API_PORT=9001
    - Entorno de Ejecución: Host (no contenedor)
    - Impacto Disruptivo: Alto

12. [x] Reconstruir y reiniciar el servicio VPN
    - Descripción: Reconstruir e iniciar el servicio VPN para aplicar el cambio de puerto
    - Dependencias: Subtarea 11
    - Recursos: Docker Compose
    - Verificación: El contenedor subnetx_vpn se reinicia con la nueva configuración
    - Entorno de Ejecución: Host (no contenedor)
    - Impacto Disruptivo: Alto

13. [x] Comprobar accesibilidad de la API VPN en el nuevo puerto 9001
    - Descripción: Verificar que la API VPN es ahora accesible desde el host en el puerto 9001
    - Dependencias: Subtarea 12
    - Recursos: curl, navegador web
    - Verificación: Se obtiene respuesta HTTP 200 OK al acceder a http://localhost:9001
    - Entorno de Ejecución: Host (no contenedor)
    - Impacto Disruptivo: Bajo

14. [x] Verificar que la API ya no es accesible en el puerto 9000
    - Descripción: Comprobar que la API VPN ya no responde en el puerto original 9000
    - Dependencias: Subtarea 13
    - Recursos: curl, navegador web
    - Verificación: No se obtiene respuesta al intentar acceder a http://localhost:9000
    - Entorno de Ejecución: Host (no contenedor)

15. [x] Restaurar la configuración original
    - Descripción: Volver a configurar el puerto de la API VPN a 9000 en el archivo .env
    - Dependencias: Subtarea 14
    - Recursos: .env
    - Verificación: El archivo .env contiene de nuevo VPN_API_PORT=9000
    - Entorno de Ejecución: Host (no contenedor)
    - Impacto Disruptivo: Medio

16. [x] Reconstruir y reiniciar el servicio con la configuración original
    - Descripción: Reconstruir e iniciar el servicio VPN para volver a la configuración original
    - Dependencias: Subtarea 15
    - Recursos: Docker Compose
    - Verificación: El contenedor subnetx_vpn se reinicia con la configuración original
    - Entorno de Ejecución: Host (no contenedor)
    - Impacto Disruptivo: Medio

17. [x] Verificar de nuevo la API en el puerto 9000
    - Descripción: Comprobar que la API VPN vuelve a ser accesible en el puerto 9000
    - Dependencias: Subtarea 16
    - Recursos: curl, navegador web
    - Verificación: Se obtiene respuesta HTTP 200 OK al acceder a http://localhost:9000
    - Entorno de Ejecución: Host (no contenedor)
    - Impacto Disruptivo: Bajo

18. [x] Documentar resultados y recomendaciones
    - Descripción: Crear documentación sobre los resultados de las pruebas y recomendaciones
    - Dependencias: Subtarea 17
    - Recursos: Editor de texto
    - Verificación: Documento con resultados y recomendaciones creado
    - Entorno de Ejecución: Host (no contenedor)
    - Impacto Disruptivo: Bajo
