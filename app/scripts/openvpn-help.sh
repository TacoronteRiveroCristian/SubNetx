#!/bin/bash
cat <<EOF
Uso: $(basename "$0") {setup|start|stop|client {new|delete} [opciones]}

Comandos:
  setup         Configura OpenVPN y genera certificados.
  start         Inicia el servicio OpenVPN.
  stop          Detiene el servicio OpenVPN.
  client new    Crea un nuevo cliente (requiere --name y --ip).
  client delete Elimina un cliente.

Opciones para "client new":
  --name <nombre>   Especifica el nombre del cliente.
  --ip   <ip>       Especifica la IP asignada al cliente.

Ejemplo:
  $(basename "$0") client new --name myclient1 --ip 10.8.0.10

EOF
