#!/bin/bash
# openvpn-menu.sh - Interfaz interactiva para gestionar OpenVPN
# Descripcion: Proporciona una interfaz de terminal para ejecutar los comandos de OpenVPN
#
# Este script utiliza whiptail para crear una interfaz de usuario por terminal (TUI)
# que permite gestionar OpenVPN de manera interactiva sin necesidad de recordar comandos.

# =========================================================================
# CONSTANTES Y VARIABLES GLOBALES
# =========================================================================

# Rutas a los scripts originales - Centraliza todas las rutas para facilitar cambios
SETUP_SCRIPT="/app/scripts/openvpn-setup.sh"           # Script de configuracion
START_SCRIPT="/app/scripts/openvpn-start.sh"           # Script para iniciar el servicio
STOP_SCRIPT="/app/scripts/openvpn-stop.sh"             # Script para detener el servicio
CLIENT_NEW_SCRIPT="/app/scripts/openvpn-client-new.sh" # Script para crear clientes
CLIENT_DEL_SCRIPT="/app/scripts/openvpn-client-delete.sh" # Script para eliminar clientes
HELP_SCRIPT="/app/scripts/openvpn-help.sh"             # Script de ayuda

# Directorio para logs temporales
LOG_DIR="/tmp/subnetx"
mkdir -p "$LOG_DIR" # Crea el directorio si no existe

# =========================================================================
# FUNCIONES UTILITARIAS
# =========================================================================

# Funcion: show_logo
# Descripcion: Muestra el logo ASCII de SubNetx
show_logo() {
    echo -e "\e[32m"  # Color verde
    cat << "EOF"
   _____       _     _   _      _
  / ____|     | |   | \ | |    | |
 | (___  _   _| |__ |  \| | ___| |___  __
  \___ \| | | | '_ \| . ` |/ _ \ __\ \/ /
  ____) | |_| | |_) | |\  |  __/ |_ >  <
 |_____/ \__,_|_.__/|_| \_|\___|\__/_/\_\

EOF
    echo -e "\e[0m"  # Resetear color
}

show_exit_message() {
    clear
    echo -e "\e[32m"  # Color verde
    echo "=================================================="
    echo "           ¡Hasta pronto! 👋                     "
    echo "=================================================="
    echo "Gracias por usar SubNetx. ¡Vuelve pronto! 🚀"
    echo "=================================================="
    echo -e "\e[0m"  # Resetear color
    show_logo
}

# Funcion: pause_before_return
# Descripcion: Pausa la ejecucion hasta que el usuario presione Enter
pause_before_return() {
    echo ""
    echo "Presione ENTER para volver al menu..."
    read
}

# =========================================================================
# FUNCIONES DEL MENU PRINCIPAL
# =========================================================================

# Funcion: show_main_menu
# Descripcion: Muestra el menu principal con todas las opciones disponibles
# Parametros: Ninguno
# Retorno: Llama a la funcion correspondiente segun la opcion seleccionada
show_main_menu() {
    OPTION=$(whiptail --title "OpenVPN Manager" --menu "Seleccione una opcion:" 15 60 6 \
        "setup" "Configurar OpenVPN" \
        "start" "Iniciar servicio" \
        "stop" "Detener servicio" \
        "client" "Gestionar clientes" \
        "help" "Ver ayuda" \
        "exit" "Salir" 3>&1 1>&2 2>&3)

    if [ $? -ne 0 ]; then
        show_exit_message
        exit 0
    fi

    case "$OPTION" in
        setup)
            run_setup
            ;;
        start)
            run_start
            ;;
        stop)
            run_stop
            ;;
        client)
            show_client_menu
            ;;
        help)
            run_help
            ;;
        exit)
            show_exit_message
            exit 0
            ;;
    esac
}

# =========================================================================
# FUNCIONES DEL SUBMENU DE CLIENTES
# =========================================================================

# Funcion: show_client_menu
# Descripcion: Muestra el submenu para gestionar clientes OpenVPN
# Parametros: Ninguno
# Retorno: Llama a la funcion correspondiente segun la opcion seleccionada
show_client_menu() {
    # Estructura similar al menu principal pero con opciones para gestion de clientes
    CLIENT_OPTION=$(whiptail --title "Gestion de Clientes" --menu "Seleccione una opcion:" 15 60 3 \
        "new" "Crear nuevo cliente" \
        "delete" "Eliminar cliente existente" \
        "back" "Volver al menu principal" 3>&1 1>&2 2>&3)

    # Si el usuario cancela, volver al menu principal
    if [ $? -ne 0 ]; then
        show_main_menu
        return
    fi

    # Navegar segun la opcion seleccionada
    case "$CLIENT_OPTION" in
        new)
            create_new_client
            ;;
        delete)
            delete_client
            ;;
        back)
            show_main_menu
            ;;
    esac
}

# =========================================================================
# FUNCIONES DE ACCION PRINCIPALES
# =========================================================================

# Funcion: run_setup
# Descripcion: Ejecuta el script de configuracion de OpenVPN
run_setup() {
    clear
    echo "---------------------------------------------------"

    $SETUP_SCRIPT
    SETUP_STATUS=$?

    echo "---------------------------------------------------"
    if [ $SETUP_STATUS -eq 0 ]; then
        echo "✅ Proceso completado exitosamente."
    else
        echo "❌ El proceso finalizo con errores (codigo: $SETUP_STATUS)."
    fi

    pause_before_return
    show_main_menu
}

# Funcion: run_start
# Descripcion: Inicia el servicio OpenVPN
run_start() {
    clear
    echo "---------------------------------------------------"

    $START_SCRIPT
    START_STATUS=$?

    echo "---------------------------------------------------"
    if [ $START_STATUS -eq 0 ]; then
        echo "✅ El servicio se inicio correctamente."
    else
        echo "❌ Ha ocurrido un error al iniciar el servicio (codigo: $START_STATUS)."
    fi

    pause_before_return
    show_main_menu
}

# Funcion: run_stop
# Descripcion: Detiene el servicio OpenVPN
run_stop() {
    clear
    echo "---------------------------------------------------"

    $STOP_SCRIPT
    STOP_STATUS=$?

    echo "---------------------------------------------------"
    if [ $STOP_STATUS -eq 0 ]; then
        echo "✅ El servicio se detuvo correctamente."
    else
        echo "❌ Ha ocurrido un error al detener el servicio (codigo: $STOP_STATUS)."
    fi

    pause_before_return
    show_main_menu
}

# =========================================================================
# FUNCIONES DE GESTION DE CLIENTES
# =========================================================================

# Funcion: create_new_client
# Descripcion: Crea un nuevo cliente OpenVPN solicitando nombre e IP
create_new_client() {
    # Pedir nombre del cliente mediante una caja de entrada de texto
    # --inputbox: Crea un campo para ingresar texto
    CLIENT_NAME=$(whiptail --title "Nuevo Cliente" --inputbox "Ingrese el nombre del cliente:" 8 50 3>&1 1>&2 2>&3)

    # Verificar si se cancelo la operacion
    if [ $? -ne 0 ]; then
        show_client_menu
        return
    fi

    # Validar que se ingreso un nombre
    if [ -z "$CLIENT_NAME" ]; then
        whiptail --title "Error" --msgbox "Debe ingresar un nombre para el cliente." 8 50
        create_new_client
        return
    fi

    # Pedir direccion IP del cliente
    CLIENT_IP=$(whiptail --title "Nuevo Cliente" --inputbox "Ingrese la direccion IP del cliente:" 8 50 3>&1 1>&2 2>&3)

    # Verificar si se cancelo la operacion
    if [ $? -ne 0 ]; then
        show_client_menu
        return
    fi

    # Validar que se ingreso una IP
    if [ -z "$CLIENT_IP" ]; then
        whiptail --title "Error" --msgbox "Debe ingresar una direccion IP para el cliente." 8 50
        create_new_client
        return
    fi

    # Mostrar confirmacion antes de proceder
    if whiptail --title "Confirmar" --yesno "¿Crear cliente con los siguientes datos?\n\nNombre: $CLIENT_NAME\nIP: $CLIENT_IP" 10 60; then
        clear
        echo "Nombre: $CLIENT_NAME"
        echo "IP: $CLIENT_IP"
        echo "---------------------------------------------------"

        $CLIENT_NEW_SCRIPT --name "$CLIENT_NAME" --ip "$CLIENT_IP"
        CLIENT_STATUS=$?

        echo "---------------------------------------------------"
        if [ $CLIENT_STATUS -eq 0 ]; then
            echo "✅ Cliente creado correctamente."
        else
            echo "❌ Ha ocurrido un error al crear el cliente (codigo: $CLIENT_STATUS)."
        fi

        pause_before_return
    fi

    show_client_menu
}

# Funcion: delete_client
# Descripcion: Elimina un cliente OpenVPN existente
delete_client() {
    # Obtener lista de clientes desde el directorio de configuraciones
    CLIENTS_DIR="/etc/openvpn/clients"
    if [ -d "$CLIENTS_DIR" ]; then
        # Buscar archivos .ovpn y eliminar la extension para obtener los nombres
        CLIENTS=$(ls -1 "$CLIENTS_DIR" | grep ".ovpn" | sed 's/\.ovpn$//')
    fi

    # Verificar si hay clientes configurados
    if [ -z "$CLIENTS" ]; then
        whiptail --title "Error" --msgbox "No se encontraron clientes configurados." 8 50
        show_client_menu
        return
    fi

    # Convertir la lista de clientes en formato para whiptail (clave descripcion)
    # Ejemplo: "cliente1 cliente1 cliente2 cliente2"
    CLIENT_OPTIONS=""
    for client in $CLIENTS; do
        CLIENT_OPTIONS="$CLIENT_OPTIONS $client $client"
    done

    # Mostrar lista de clientes para seleccionar en un menu
    SELECTED_CLIENT=$(whiptail --title "Eliminar Cliente" --menu "Seleccione el cliente a eliminar:" 15 60 6 $CLIENT_OPTIONS 3>&1 1>&2 2>&3)

    # Verificar si se cancelo la operacion
    if [ $? -ne 0 ]; then
        show_client_menu
        return
    fi

    # Pedir confirmacion antes de eliminar
    if whiptail --title "Confirmar" --yesno "¿Esta seguro de que desea eliminar el cliente '$SELECTED_CLIENT'?" 8 60; then
        clear
        echo "Cliente: $SELECTED_CLIENT"
        echo "---------------------------------------------------"

        $CLIENT_DEL_SCRIPT "$SELECTED_CLIENT"
        DEL_STATUS=$?

        echo "---------------------------------------------------"
        if [ $DEL_STATUS -eq 0 ]; then
            echo "✅ Cliente eliminado correctamente."
        else
            echo "❌ Ha ocurrido un error al eliminar el cliente (codigo: $DEL_STATUS)."
        fi

        pause_before_return
    fi

    show_client_menu
}

# Funcion: run_help
# Descripcion: Muestra la ayuda de OpenVPN
run_help() {
    # Capturar la salida del script de ayuda
    HELP_OUTPUT=$($HELP_SCRIPT)

    # Mostrar la ayuda en una ventana de texto desplazable
    # --scrolltext: Permite desplazar el texto con las flechas
    whiptail --title "Ayuda de OpenVPN" --scrolltext --msgbox "$HELP_OUTPUT" 20 70

    # Volver al menu principal
    show_main_menu
}

# =========================================================================
# VERIFICACIONES INICIALES Y PUNTO DE ENTRADA
# =========================================================================

# Verificar que whiptail esta instalado
if ! command -v whiptail &> /dev/null; then
    echo "Error: whiptail no esta instalado. Por favor, instalelo con:"
    echo "apt-get install whiptail"
    exit 1
fi

# Punto de entrada: Iniciar la interfaz mostrando el menu principal
show_main_menu
