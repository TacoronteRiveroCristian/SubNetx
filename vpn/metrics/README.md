# SubNetx Network Monitoring System

Un sistema completo de monitorización de redes para VPNs que recopila métricas detalladas sobre conectividad, rendimiento y estabilidad de conexiones de red.

## Características

- **Monitorización de ping**: Mide latencia, pérdida de paquetes y calidad de conexión
- **Tráfico de red**: Monitoriza bytes/paquetes enviados y recibidos, y tasas de transferencia
- **Ancho de banda**: Mide velocidades de descarga/subida y jitter
- **Estado de conexión**: Seguimiento de tiempos de conexión, desconexiones y estabilidad
- **Logging centralizado**: Sistema unificado de logs para todas las métricas
- **Análisis de estabilidad**: Evaluación de la calidad y estabilidad de la conexión

## Requisitos

- Python 3.6+
- Dependencias listadas en `requirements.txt`

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/yourusername/subnetx.git
cd subnetx/vpn/metrics

# Instalar dependencias
pip install -r requirements.txt
```

## Uso

```bash
# Monitorizar un host específico
python main.py --target google.com

# Personalizar el intervalo de monitorización
python main.py --target 8.8.8.8 --interval 30

# Ejecutar monitorización por un tiempo limitado
python main.py --target 192.168.1.1 --duration 3600
```

## Estructura del proyecto

```
metrics/
├── main.py              # Punto de entrada principal y configuración
├── collector/           # Módulos de recolección de métricas
│   ├── __init__.py      # Definición del paquete
│   ├── ping.py          # Monitorización de ping y latencia
│   ├── traffic.py       # Análisis de tráfico de red
│   ├── bandwidth.py     # Medición de ancho de banda
│   └── connection.py    # Seguimiento de estado de conexión
└── requirements.txt     # Dependencias del proyecto
```

## Personalización

Cada módulo puede ejecutarse independientemente para pruebas o monitorización específica. Por ejemplo:

```bash
# Ejecutar solo monitorización de ping
python -m collector.ping
```
