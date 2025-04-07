#!/bin/bash

# Script para probar el extractor de ping mejorado
# Uso: ./test_ping.sh [objetivo1] [objetivo2] ...

# Definir colores para mejor visibilidad
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== SubNetx VPN - Test de Extractor de Ping ===${NC}"
echo

# Comprobar si se proporciona al menos un objetivo
if [ $# -ge 1 ]; then
    TARGETS="$@"
else
    # Usar dominios predeterminados si no se proporciona ninguno
    TARGETS="google.com cloudflare.com"
    echo -e "${YELLOW}No se proporcionaron objetivos. Usando dominios predeterminados: ${TARGETS}${NC}"
fi

echo -e "${GREEN}Ejecutando pruebas para los siguientes objetivos: ${TARGETS}${NC}"
echo

# Ejecutar el script de prueba con los objetivos proporcionados
python -m vpn.metrics.collector.test_ping_extractor $TARGETS

# Comprobar si la ejecución fue exitosa
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Pruebas completadas correctamente.${NC}"
else
    echo -e "${RED}Error al ejecutar las pruebas.${NC}"
    exit 1
fi

echo
echo -e "${GREEN}=== Pruebas Finalizadas ===${NC}"
