/**
 * Server Management page component
 * Allows admin users to control and configure the OpenVPN server
 */
import Head from 'next/head';
import { useRouter } from 'next/router';
import React, { useCallback, useEffect, useState } from 'react';
import BackgroundEffect from '../components/BackgroundEffect';
import Footer from '../components/Footer';
import Logo from '../components/Logo';

// Define theme object
const themes = {
    light: {
        background: '#ffffff',
        text: '#1a1a1a',           // Cambiado de #333333 a #1a1a1a para mejor contraste
        primary: '#2E7D32',        // Verde más oscuro para mejor contraste
        secondary: '#1565C0',      // Azul más oscuro para mejor contraste
        border: '#e0e0e0',         // Borde más visible
        tableHeader: '#f5f5f5',
        tableRow: '#ffffff',
        tableRowHover: '#f5f5f5',
        cardBackground: '#ffffff',
        errorBackground: '#FFEBEE',
        statusIndicator: '#E3F2FD',
        navbar: '#ffffff',
        buttonHover: '#f0f0f0',
        borderLight: '#ccc',
    },
    dark: {
        background: '#1a1a1a',
        text: '#ffffff',
        primary: '#66bb6a',
        secondary: '#42a5f5',
        border: '#333333',
        tableHeader: '#2d2d2d',
        tableRow: '#1a1a1a',
        tableRowHover: '#2d2d2d',
        cardBackground: '#2d2d2d',
        errorBackground: '#311111',
        statusIndicator: '#1a237e',
        navbar: '#1a1a1a',
        buttonHover: '#2d2d2d',
        borderLight: '#444',
    },
};

// Define client type
interface Client {
    name: string;
    ip: string;
    created_at: string;
}

export default function ServerManagement() {
    // Initialize router for navigation
    const router = useRouter();

    // State variables
    const [loading, setLoading] = useState(false);
    const [theme, setTheme] = useState<'light' | 'dark'>('dark');
    const [isHamburgerOpen, setIsHamburgerOpen] = useState(false);
    const [serverStatus, setServerStatus] = useState<'running' | 'stopped' | 'unknown'>('unknown');
    const [serverHasCertificates, setServerHasCertificates] = useState(false);
    const [clients, setClients] = useState<Client[]>([]);
    const [serverConfig, setServerConfig] = useState({
        vpn_network: "",
        vpn_netmask: "",
        openvpn_port: 0,
        openvpn_proto: "",
        public_ip: ""
    });

    // Cliente modal states
    const [createClientModalOpen, setCreateClientModalOpen] = useState(false);
    const [newClientName, setNewClientName] = useState('');
    const [newClientIP, setNewClientIP] = useState('');
    const [clientCreating, setClientCreating] = useState(false);
    const [clientError, setClientError] = useState<string | null>(null);

    // Setup modal states
    const [setupModalOpen, setSetupModalOpen] = useState(false);
    const [setupConfirmModalOpen, setSetupConfirmModalOpen] = useState(false);
    const [setupVpnNetwork, setSetupVpnNetwork] = useState('');
    const [setupVpnNetmask, setSetupVpnNetmask] = useState('');
    const [setupOpenvpnPort, setSetupOpenvpnPort] = useState('');
    const [setupOpenvpnProto, setSetupOpenvpnProto] = useState('udp');
    const [setupPublicIp, setSetupPublicIp] = useState('');
    const [setupError, setSetupError] = useState<string | null>(null);
    const [setupProcessing, setSetupProcessing] = useState(false);

    // Delete configuration states
    const [deleteConfirmModalOpen, setDeleteConfirmModalOpen] = useState(false);
    const [deleteProcessing, setDeleteProcessing] = useState(false);
    const [deleteError, setDeleteError] = useState<string | null>(null);

    const [notification, setNotification] = useState<{
        message: string;
        type: 'success' | 'error';
        visible: boolean;
    }>({ message: '', type: 'success', visible: false });

    // Error handling state
    const [errorLog, setErrorLog] = useState<{ message: string, timestamp: Date, retryCount: number }[]>([]);

    // Client loading states
    const [clientsLoading, setClientsLoading] = useState(false);
    const [lastClientUpdate, setLastClientUpdate] = useState<Date | null>(null);

    // Delete client states
    const [deletingClient, setDeletingClient] = useState<string | null>(null);
    const [deleteClientConfirmOpen, setDeleteClientConfirmOpen] = useState(false);
    const [clientToDelete, setClientToDelete] = useState<string>('');

    // Centralized error handler function
    const handleError = (operation: string, error: any, retry?: boolean, retryFn?: () => Promise<void>, maxRetries = 3) => {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error(`Error during ${operation}:`, error);

        // Add to error log
        const newError = {
            message: `${operation} failed: ${errorMessage}`,
            timestamp: new Date(),
            retryCount: 0
        };

        setErrorLog(prev => {
            // Limit length of error log to prevent it growing too large
            const updatedLog = [...prev, newError];
            if (updatedLog.length > 10) {
                return updatedLog.slice(updatedLog.length - 10);
            }
            return updatedLog;
        });

        // Show notification
        showNotification(`${operation} failed: ${errorMessage}`, 'error');

        // Attempt retry if specified
        if (retry && retryFn) {
            const existingErrors = errorLog.filter(e => e.message.startsWith(`${operation} failed`));
            const retryCount = existingErrors.length;

            if (retryCount < maxRetries) {
                console.log(`Retrying ${operation} (attempt ${retryCount + 1}/${maxRetries})...`);
                setTimeout(() => {
                    retryFn().catch(retryError => {
                        handleError(`${operation} (retry ${retryCount + 1})`, retryError);
                    });
                }, 2000 * (retryCount + 1)); // Exponential backoff
            } else {
                console.log(`Maximum retry attempts (${maxRetries}) reached for ${operation}`);
                showNotification(`Maximum retry attempts reached for ${operation}`, 'error');
            }
        }
    };

    // Get current theme
    const currentTheme = themes[theme];

    // Function to refresh server status
    const refreshServerStatus = useCallback(async () => {
        try {
            console.log('Refreshing server status...');
            const response = await fetch('/api/vpn/status');

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Server status response:', data);

            // Update the status based on the API response which includes details.status.state
            if (data.details && data.details.status && data.details.status.state) {
                setServerStatus(data.details.status.state === 'running' ? 'running' : 'stopped');
            } else if (data.status) {
                // Fallback to older API format if available
                setServerStatus(data.status as 'running' | 'stopped' | 'unknown');
            }

            // Si la API devuelve información sobre los certificados, actualizamos el estado
            if (data.hasCertificates !== undefined) {
                setServerHasCertificates(data.hasCertificates);
            }

            // If status is running, try to get configuration
            if ((data.details && data.details.status && data.details.status.state === 'running') || data.status === 'running') {
                if (data.config) {
                    const config = {
                        vpn_network: data.config.vpn_network || "",
                        vpn_netmask: data.config.vpn_netmask || "",
                        openvpn_port: data.config.openvpn_port || 0,
                        openvpn_proto: data.config.openvpn_proto || "",
                        public_ip: data.config.public_ip || ""
                    };

                    setServerConfig(config);
                    localStorage.setItem('serverConfig', JSON.stringify(config));
                }
            }
        } catch (error) {
            console.error('Failed to refresh server status:', error);
        }
    }, []);

    // Refresh status when navigating to the page
    useEffect(() => {
        if (router.asPath === '/server') {
            refreshServerStatus();
        }
    }, [router.asPath, refreshServerStatus]);

    // Check authentication on mount and ensure user is admin
    useEffect(() => {
        const checkAuth = async () => {
            // Check if user is authenticated and is admin
            if (localStorage.getItem('isAuthenticated') !== 'true') {
                router.push('/login');
                return;
            }

            // Check if user is admin
            if (localStorage.getItem('userRole') !== 'admin') {
                router.push('/dashboard');
                return;
            }

            // Refresh server status instead of directly fetching
            await refreshServerStatus();

            // Try to load configuration from localStorage if not available from API
            if (serverStatus !== 'running') {
                const savedConfig = localStorage.getItem('serverConfig');
                if (savedConfig) {
                    setServerConfig(JSON.parse(savedConfig));
                }
            }
        };

        checkAuth();
    }, [router, refreshServerStatus, serverStatus]);

    // Load theme from localStorage
    useEffect(() => {
        // Check if theme preference exists in localStorage
        const savedTheme = localStorage.getItem('appTheme');
        if (savedTheme === 'light' || savedTheme === 'dark') {
            setTheme(savedTheme);
            document.documentElement.setAttribute('data-theme', savedTheme);
        }
    }, []);

    // Toggle theme function
    const toggleTheme = () => {
        const newTheme = theme === 'light' ? 'dark' : 'light';
        // Save theme preference to localStorage
        localStorage.setItem('appTheme', newTheme);
        // Update state
        setTheme(newTheme);
        // Update document attribute for CSS
        document.documentElement.setAttribute('data-theme', newTheme);
    };

    // Function to handle logout
    const handleLogout = async () => {
        try {
            // Restaurar el tema oscuro por defecto antes de cerrar sesión
            localStorage.setItem('appTheme', 'dark');

            // Limpiar localStorage primero
            localStorage.removeItem('isAuthenticated');
            localStorage.removeItem('userRole');
            localStorage.removeItem('userId');

            // PRIMERO hacer la llamada al API de logout para invalidar la sesión
            // y esperar a que termine antes de redirigir
            await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include',
            });

            // Finalmente redirigir al usuario después de limpiar todo
            window.location.replace('/login');
        } catch (error) {
            // Si hay un error, asegurar que el usuario sea redirigido de todas formas
            // Intentar limpiar las cookies localmente primero
            localStorage.removeItem('isAuthenticated');
            localStorage.removeItem('userRole');
            localStorage.removeItem('userId');

            window.location.replace('/login');
        }
    };

    // Función para mostrar notificaciones
    const showNotification = (message: string, type: 'success' | 'error') => {
        setNotification({ message, type, visible: true });

        // Ocultar automáticamente después de 5 segundos
        setTimeout(() => {
            setNotification((prev: { message: string; type: 'success' | 'error'; visible: boolean }) => ({ ...prev, visible: false }));
        }, 5000);
    };

    // Server operations function
    const handleServerOperation = async (operation: 'setup' | 'start' | 'stop' | 'edit') => {
        // Para el caso de setup, verificamos si hay certificados existentes
        if (operation === 'setup') {
            // Si hay certificados existentes, mostramos primero el modal de confirmación
            if (serverHasCertificates) {
                setSetupConfirmModalOpen(true);
            } else {
                // Si no hay certificados, mostramos directamente el modal de configuración
                setSetupModalOpen(true);
            }
            return;
        }

        setLoading(true);

        try {
            let endpoint = '';
            switch (operation) {
                case 'start':
                    endpoint = '/api/vpn/start';
                    break;
                case 'stop':
                    endpoint = '/api/vpn/stop';
                    break;
                case 'edit':
                    // Simulate API call with timeout for edit operation only
                    setTimeout(() => {
                        setLoading(false);
                    }, 1500);
                    return;
                default:
                    throw new Error(`Unsupported operation: ${operation}`);
            }

            // Realizar la llamada a la API
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                // Actualizar el estado según la operación
                if (operation === 'start') {
                    setServerStatus('running');
                    showNotification('Server started successfully', 'success');
                } else if (operation === 'stop') {
                    setServerStatus('stopped');
                    showNotification('Server stopped successfully', 'success');

                    // Refresh server status to confirm
                    setTimeout(refreshServerStatus, 500);
                }
            } else {
                // Manejar error con el sistema centralizado
                handleError(`${operation} server`, new Error(data.error || data.message || 'Operation failed'));
            }
        } catch (error) {
            // Usar el sistema centralizado de manejo de errores
            handleError(`${operation} server`, error, operation === 'stop', async () => {
                await handleServerOperation(operation);
            });
        } finally {
            setLoading(false);
        }
    };

    // Function to handle delete configuration
    const handleDeleteConfiguration = async () => {
        setDeleteProcessing(true);
        setDeleteError(null);

        try {
            // Call the API endpoint to cleanup configuration
            const response = await fetch('/api/vpn/cleanup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                // Update server state
                setServerHasCertificates(false);
                setServerStatus('stopped');

                // Reset server configuration - usar strings vacíos para que se muestren guiones
                const emptyConfig = {
                    vpn_network: "",
                    vpn_netmask: "",
                    openvpn_port: 0,
                    openvpn_proto: "",
                    public_ip: ""
                };

                setServerConfig(emptyConfig);
                // Limpiar la lista de clientes
                setClients([]);

                // Eliminar la configuración del localStorage
                localStorage.removeItem('serverConfig');

                showNotification('Server configuration cleaned up successfully', 'success');

                // Close the modal
                setDeleteConfirmModalOpen(false);
            } else {
                const errorMsg = data.message || 'Error cleaning up server configuration';
                setDeleteError(errorMsg);
                handleError('Cleaning up server configuration', new Error(errorMsg));
            }
        } catch (error) {
            setDeleteError('Failed to connect to server');
            handleError('Cleaning up server configuration', error);
        } finally {
            setDeleteProcessing(false);
        }
    };

    // Function to handle setup confirmation
    const handleConfirmSetup = () => {
        // Cerramos el modal de confirmación
        setSetupConfirmModalOpen(false);
        // Abrimos el modal de configuración
        setSetupModalOpen(true);
    };

    // Function to handle setup form submission
    const handleSetupSubmit = async () => {
        // Validar los campos del formulario
        if (!setupVpnNetwork) {
            setSetupError('VPN Network is required');
            return;
        }
        if (!setupVpnNetmask) {
            setSetupError('VPN Netmask is required');
            return;
        }
        if (!setupOpenvpnPort) {
            setSetupError('OpenVPN Port is required');
            return;
        }
        // Validar que el puerto sea un número entre 1-65535
        const port = parseInt(setupOpenvpnPort);
        if (isNaN(port) || port < 1 || port > 65535) {
            setSetupError('Port must be a number between 1-65535');
            return;
        }
        if (!setupOpenvpnProto) {
            setSetupError('OpenVPN Protocol is required');
            return;
        }
        if (!setupPublicIp) {
            setSetupError('Public IP/Domain is required');
            return;
        }

        setSetupProcessing(true);
        setSetupError(null);

        try {
            const endpoint = '/api/vpn/setup';
            const body = {
                vpn_network: setupVpnNetwork,
                vpn_netmask: setupVpnNetmask,
                openvpn_port: parseInt(setupOpenvpnPort),
                openvpn_proto: setupOpenvpnProto,
                tun_device: "tun0", // Valor por defecto para tun_device
                public_ip: setupPublicIp,
                force_reset: serverHasCertificates // Si había certificados, indicamos que debe forzar reset
            };

            console.log(`Calling VPN setup endpoint with body:`, body);

            // Realizar la llamada a la API
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(body)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                // Crear objeto de configuración
                const newConfig = {
                    vpn_network: setupVpnNetwork,
                    vpn_netmask: setupVpnNetmask,
                    openvpn_port: parseInt(setupOpenvpnPort),
                    openvpn_proto: setupOpenvpnProto,
                    public_ip: setupPublicIp
                };

                // Actualizar la configuración del servidor
                setServerConfig(newConfig);

                // Guardar la configuración en localStorage para persistencia
                localStorage.setItem('serverConfig', JSON.stringify(newConfig));

                // Cerrar el modal y mostrar notificación
                setSetupModalOpen(false);

                // Si se ha forzado el reset, mostramos un mensaje específico
                if (serverHasCertificates) {
                    showNotification('Server reconfigured and all clients reset successfully', 'success');
                } else {
                    showNotification('Server configured successfully', 'success');
                }

                // Actualizamos el estado de certificados
                setServerHasCertificates(true);

                // Resetear el estado del formulario
                resetSetupForm();
            } else {
                // Mostrar mensaje de error
                setSetupError(data.message || 'Error configuring server');
            }
        } catch (error) {
            console.error('Failed to configure server:', error);
            setSetupError('Failed to connect to server');
        } finally {
            setSetupProcessing(false);
        }
    };

    // Function to reset setup form
    const resetSetupForm = () => {
        setSetupVpnNetwork('');
        setSetupVpnNetmask('');
        setSetupOpenvpnPort('');
        setSetupOpenvpnProto('udp');
        setSetupPublicIp('');
        setSetupError(null);
    };

    // Function to load clients
    const loadClients = async () => {
        try {
            setClientsLoading(true);
            const response = await fetch('/api/vpn/clients');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Clients data:', data);

            // Transform API response to client array
            if (data.details && data.details.clients) {
                const clientsObject = data.details.clients;
                const clientsArray = Object.keys(clientsObject).map(name => ({
                    name: name,
                    ip: clientsObject[name].ip_address || clientsObject[name].ip || '',
                    created_at: clientsObject[name].creation_date || clientsObject[name].created_at || new Date().toISOString()
                }));
                setClients(clientsArray);
            } else if (Array.isArray(data)) {
                // Handle case where data is already an array
                setClients(data);
            } else {
                // If data format is unexpected, set empty array
                console.warn('Unexpected clients data format:', data);
                setClients([]);
            }

            setLastClientUpdate(new Date());
        } catch (error) {
            // Use centralized error handling
            handleError('Loading clients', error, true, loadClients);
            // If there's an error, set clients to an empty array to prevent issues
            setClients([]);
        } finally {
            setClientsLoading(false);
        }
    };

    // Setup clients loading only on mount
    useEffect(() => {
        // Load clients just once on component mount
        loadClients();

        // No automatic refresh interval
    }, []);

    // Also load clients after server status changes or operations that affect them
    useEffect(() => {
        if (serverStatus !== 'unknown') {
            loadClients();
        }
    }, [serverStatus]);

    // Función para validar si una IP está dentro de la red VPN
    const isIPInVPNNetwork = (ip: string): boolean => {
        if (!serverConfig.vpn_network || !serverConfig.vpn_netmask) return false;

        try {
            const network = `${serverConfig.vpn_network}/${serverConfig.vpn_netmask}`;
            const clientIP = ip;
            return clientIP.startsWith(serverConfig.vpn_network.split('.').slice(0, 3).join('.'));
        } catch (error) {
            console.error('Error validating IP:', error);
            return false;
        }
    };

    // Function to create a new client
    const handleCreateClient = async () => {
        if (!newClientName || !newClientIP) {
            setClientError('Please fill in all fields');
            return;
        }

        // Validate name format (only letters, numbers, hyphens and underscores)
        if (!/^[a-zA-Z0-9_-]+$/.test(newClientName)) {
            setClientError('Client name can only contain letters, numbers, hyphens and underscores');
            return;
        }

        // Validate IP format
        const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
        if (!ipRegex.test(newClientIP)) {
            setClientError('Invalid IP format');
            return;
        }

        // Verify if IP is within VPN network
        if (!isIPInVPNNetwork(newClientIP)) {
            setClientError(`IP ${newClientIP} is not within the configured VPN network (${serverConfig.vpn_network})`);
            return;
        }

        // Check if name or IP already exists
        const existingClient = Array.isArray(clients)
            ? clients.find(client => client.name === newClientName || client.ip === newClientIP)
            : undefined;
        if (existingClient) {
            if (existingClient.name === newClientName) {
                setClientError(`A client with name ${newClientName} already exists`);
            } else {
                setClientError(`IP ${newClientIP} is already assigned to client ${existingClient.name}`);
            }
            return;
        }

        try {
            const response = await fetch('/api/vpn/client/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: newClientName,
                    ip: newClientIP,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error creating client');
            }

            const data = await response.json();
            setClientError('');
            setNewClientName('');
            setNewClientIP('');
            loadClients(); // Reload clients list
            showNotification(`Client ${newClientName} created successfully`, 'success');
            setCreateClientModalOpen(false); // Close the modal
        } catch (error) {
            setClientError(error instanceof Error ? error.message : 'Error creating client');
        }
    };

    return (
        <>
            <Head>
                <title>Server Management - SubNetx</title>
                <meta name="description" content="Manage OpenVPN Server" />
                <link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons" />
                <style>{`
          body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            overflow: hidden;
            height: 100vh;
            width: 100vw;
          }
          #__next {
            height: 100%;
            width: 100%;
            position: relative;
          }
          .background-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            background-color: ${currentTheme.background};
            transition: background-color 0.3s ease;
            overflow: hidden;
          }
          .content-container {
            position: relative;
            z-index: 1;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            background: transparent;
            overflow-y: auto;
            max-height: 100vh;
            padding-bottom: 65px; /* Add padding to prevent content from being hidden behind the fixed footer */
          }
          .nav-button {
            background: none;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            color: ${currentTheme.text};
            display: flex;
            align-items: center;
            gap: 6px;
            cursor: pointer;
            transition: background-color 0.2s;
          }
          .nav-button:hover {
            background-color: ${currentTheme.buttonHover};
          }
          .material-icons {
            font-size: 18px;
          }
          @keyframes pulse {
            0% { opacity: 0.6; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.02); }
            100% { opacity: 0.6; transform: scale(1); }
          }
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          @keyframes slideIn {
            from { transform: translateX(100%); }
            to { transform: translateX(0); }
          }
          @keyframes slideOut {
            from { transform: translateX(0); }
            to { transform: translateX(100%); }
          }
          @keyframes fadeIn {
            from { opacity: 0; transform: translate(-50%, -10px); }
            to { opacity: 1; transform: translate(-50%, 0); }
          }
          .hamburger-menu {
            animation: slideIn 0.3s ease forwards;
          }
          .hamburger-menu.closing {
            animation: slideOut 0.3s ease forwards;
          }
          .server-action-button {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
            border-radius: 12px;
            background-color: ${currentTheme.cardBackground};
            border: 1px solid ${currentTheme.border};
            color: ${currentTheme.text};
            transition: all 0.3s ease;
            cursor: pointer;
            gap: 12px;
            height: 140px;
          }
          .server-action-button:hover {
            transform: translateY(-4px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
          }
          .server-action-button.setup {
            border-color: ${currentTheme.secondary}60;
            background-color: ${currentTheme.secondary}10;
          }
          .server-action-button.setup:hover {
            background-color: ${currentTheme.secondary}20;
          }
          .server-action-button.start {
            border-color: ${currentTheme.primary}60;
            background-color: ${currentTheme.primary}10;
          }
          .server-action-button.start:hover {
            background-color: ${currentTheme.primary}20;
          }
          .server-action-button.stop {
            border-color: #F4433660;
            background-color: #F4433610;
          }
          .server-action-button.stop:hover {
            background-color: #F4433620;
          }
          .server-action-button.client {
            border-color: #FF980060;
            background-color: #FF980010;
          }
          .server-action-button.client:hover {
            background-color: #FF980020;
          }
          .server-action-button.edit {
            border-color: #9C27B060;
            background-color: #9C27B010;
          }
          .server-action-button.edit:hover {
            background-color: #9C27B020;
          }
          .status-indicator {
            padding: 4px 8px;
            border-radius: 12px;
            font-weight: 500;
            font-size: 0.75rem;
            opacity: 0.9;
            transition: all 0.2s ease;
          }
          .status-indicator.running {
            background-color: ${currentTheme.primary}15;
            color: ${currentTheme.primary};
            border: 1px solid ${currentTheme.primary}30;
          }
          .status-indicator.stopped {
            background-color: #F4433610;
            color: #F4433690;
            border: 1px solid #F4433630;
          }
          .status-indicator.unknown {
            background-color: #78909C15;
            color: #78909C;
            border: 1px solid #78909C30;
          }
          .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.7);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
          }
          .modal-content {
            background-color: ${currentTheme.background};
            border-radius: 8px;
            padding: 24px;
            width: 90%;
            max-width: 500px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
          }
        `}</style>
            </Head>

            <div className="background-container">
                <BackgroundEffect
                    theme={{
                        background: currentTheme.background,
                        primary: currentTheme.primary
                    }}
                />
            </div>

            <div className="content-container">
                {/* Header/Navbar */}
                <div style={{
                    backgroundColor: `${currentTheme.navbar}99`,
                    backdropFilter: 'blur(10px)',
                    padding: '0.5rem 1.5rem',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                    position: 'sticky',
                    top: 0,
                    zIndex: 1000,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
                        <Logo theme={{ primary: currentTheme.primary }} size="small" />
                    </div>

                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                        <button
                            onClick={() => router.push('/dashboard')}
                            className="nav-button"
                        >
                            <span className="material-icons" style={{ fontSize: '20px', marginRight: '6px' }}>
                                dashboard
                            </span>
                            <span style={{ fontSize: '0.9rem' }}>Dashboard</span>
                        </button>

                        <button
                            onClick={() => setIsHamburgerOpen(!isHamburgerOpen)}
                            className="nav-button"
                            style={{
                                padding: '8px',
                                borderRadius: '8px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                            }}
                        >
                            <span className="material-icons" style={{
                                fontSize: '22px',
                                transform: isHamburgerOpen ? 'rotate(180deg)' : 'none',
                                transition: 'transform 0.3s ease'
                            }}>
                                menu
                            </span>
                        </button>
                    </div>
                </div>

                {/* Notificación en línea */}
                {notification.visible && (
                    <div style={{
                        backgroundColor: notification.type === 'success' ? 'rgba(67, 160, 71, 0.5)' : 'rgba(229, 57, 53, 0.5)',
                        color: 'white',
                        padding: '8px 16px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        width: '70%',
                        maxWidth: '700px',
                        boxSizing: 'border-box',
                        boxShadow: '0 1px 8px rgba(0,0,0,0.15)',
                        zIndex: 999,
                        position: 'absolute',
                        top: '75px',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        borderRadius: '6px',
                        backdropFilter: 'blur(5px)',
                        animation: 'fadeIn 0.3s ease',
                        fontSize: '0.95rem'
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span className="material-icons" style={{ fontSize: '18px' }}>
                                {notification.type === 'success' ? 'check_circle' : 'error'}
                            </span>
                            {notification.message}
                        </div>
                        <button
                            onClick={() => setNotification((prev: { message: string; type: 'success' | 'error'; visible: boolean }) => ({ ...prev, visible: false }))}
                            style={{
                                background: 'none',
                                border: 'none',
                                color: 'white',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                padding: '2px'
                            }}
                        >
                            <span className="material-icons" style={{ fontSize: '16px' }}>close</span>
                        </button>
                    </div>
                )}

                {/* Hamburger Menu Overlay */}
                {isHamburgerOpen && (
                    <div
                        onClick={() => setIsHamburgerOpen(false)}
                        style={{
                            position: 'fixed',
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            backgroundColor: 'rgba(0, 0, 0, 0.5)',
                            backdropFilter: 'blur(2px)',
                            zIndex: 998,
                            opacity: isHamburgerOpen ? 1 : 0,
                            transition: 'opacity 0.3s ease'
                        }}
                    />
                )}

                {/* Hamburger Menu */}
                <div
                    className={`hamburger-menu ${!isHamburgerOpen ? 'closing' : ''}`}
                    style={{
                        position: 'fixed',
                        top: '60px',
                        right: 0,
                        width: '320px',
                        maxHeight: 'calc(100vh - 60px)',
                        backgroundColor: `${currentTheme.background}`,
                        backdropFilter: 'blur(10px)',
                        borderLeft: `1px solid ${currentTheme.border}`,
                        padding: '1.5rem',
                        zIndex: 999,
                        display: isHamburgerOpen ? 'flex' : 'none',
                        flexDirection: 'column',
                        gap: '1rem',
                        boxShadow: '-2px 0 8px rgba(0,0,0,0.2)',
                        transform: isHamburgerOpen ? 'translateX(0)' : 'translateX(100%)',
                        transition: 'transform 0.3s ease',
                        overflowY: 'auto',
                        overflowX: 'hidden'
                    }}
                >
                    <div style={{
                        position: 'sticky',
                        top: 0,
                        backgroundColor: `${currentTheme.background}`,
                        backdropFilter: 'blur(10px)',
                        paddingBottom: '1.5rem',
                        marginBottom: '0.5rem',
                        borderBottom: `1px solid ${currentTheme.border}`,
                        zIndex: 2
                    }}>
                        <div
                            onClick={() => setIsHamburgerOpen(false)}
                            style={{
                                margin: 0,
                                fontSize: '1.1rem',
                                color: currentTheme.text,
                                fontWeight: '500',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                cursor: 'pointer',
                                padding: '0.5rem 0',
                                transition: 'all 0.2s ease'
                            }}
                            onMouseEnter={(e: React.MouseEvent<HTMLDivElement>) => {
                                e.currentTarget.style.opacity = '0.8';
                                e.currentTarget.style.transform = 'translateX(-4px)';
                            }}
                            onMouseLeave={(e: React.MouseEvent<HTMLDivElement>) => {
                                e.currentTarget.style.opacity = '1';
                                e.currentTarget.style.transform = 'translateX(0)';
                            }}
                        >
                            <span className="material-icons" style={{
                                fontSize: '20px',
                                color: currentTheme.primary,
                                transition: 'transform 0.3s ease'
                            }}>
                                menu
                            </span>
                            Menu
                        </div>
                    </div>

                    <div style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '1rem',
                        flex: 1,
                        minHeight: 'min-content'
                    }}>
                        <button
                            onClick={() => router.push('/dashboard')}
                            className="nav-button"
                            style={{
                                width: '100%',
                                justifyContent: 'flex-start',
                                padding: '1rem 1.25rem',
                                borderRadius: '12px',
                                transition: 'all 0.2s ease',
                                fontSize: '1rem',
                                backgroundColor: `${currentTheme.primary}15`,
                                border: `1px solid ${currentTheme.primary}30`,
                                color: currentTheme.primary
                            }}
                            onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => {
                                e.currentTarget.style.backgroundColor = `${currentTheme.primary}25`;
                                e.currentTarget.style.transform = 'translateX(4px)';
                                e.currentTarget.style.boxShadow = `0 4px 12px ${currentTheme.primary}20`;
                            }}
                            onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => {
                                e.currentTarget.style.backgroundColor = `${currentTheme.primary}15`;
                                e.currentTarget.style.transform = 'translateX(0)';
                                e.currentTarget.style.boxShadow = 'none';
                            }}
                        >
                            <span className="material-icons" style={{
                                transition: 'transform 0.3s ease',
                                fontSize: '24px',
                                marginRight: '12px'
                            }}>
                                dashboard
                            </span>
                            Dashboard
                        </button>

                        <button
                            onClick={() => router.push('/users')}
                            className="nav-button"
                            style={{
                                width: '100%',
                                justifyContent: 'flex-start',
                                padding: '1rem 1.25rem',
                                borderRadius: '12px',
                                transition: 'all 0.2s ease',
                                fontSize: '1rem',
                                backgroundColor: `${currentTheme.secondary}15`,
                                border: `1px solid ${currentTheme.secondary}30`,
                                color: currentTheme.secondary
                            }}
                            onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => {
                                e.currentTarget.style.backgroundColor = `${currentTheme.secondary}25`;
                                e.currentTarget.style.transform = 'translateX(4px)';
                                e.currentTarget.style.boxShadow = `0 4px 12px ${currentTheme.secondary}20`;
                            }}
                            onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => {
                                e.currentTarget.style.backgroundColor = `${currentTheme.secondary}15`;
                                e.currentTarget.style.transform = 'translateX(0)';
                                e.currentTarget.style.boxShadow = 'none';
                            }}
                        >
                            <span className="material-icons" style={{
                                transition: 'transform 0.3s ease',
                                fontSize: '24px',
                                marginRight: '12px'
                            }}>
                                people
                            </span>
                            Users
                        </button>

                        <button
                            onClick={() => router.push('/server')}
                            className="nav-button"
                            style={{
                                width: '100%',
                                justifyContent: 'flex-start',
                                padding: '1rem 1.25rem',
                                borderRadius: '12px',
                                transition: 'all 0.2s ease',
                                fontSize: '1rem',
                                backgroundColor: `${currentTheme.secondary}15`,
                                border: `1px solid ${currentTheme.secondary}30`,
                                color: currentTheme.secondary
                            }}
                            onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => {
                                e.currentTarget.style.backgroundColor = `${currentTheme.secondary}25`;
                                e.currentTarget.style.transform = 'translateX(4px)';
                                e.currentTarget.style.boxShadow = `0 4px 12px ${currentTheme.secondary}20`;
                            }}
                            onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => {
                                e.currentTarget.style.backgroundColor = `${currentTheme.secondary}15`;
                                e.currentTarget.style.transform = 'translateX(0)';
                                e.currentTarget.style.boxShadow = 'none';
                            }}
                        >
                            <span className="material-icons" style={{
                                transition: 'transform 0.3s ease',
                                fontSize: '24px',
                                marginRight: '12px'
                            }}>
                                vpn_lock
                            </span>
                            Edit Server
                        </button>

                        <button
                            onClick={toggleTheme}
                            className="nav-button"
                            style={{
                                width: '100%',
                                justifyContent: 'flex-start',
                                padding: '1rem 1.25rem',
                                borderRadius: '12px',
                                transition: 'all 0.2s ease',
                                fontSize: '1rem',
                                backgroundColor: `${currentTheme.primary}15`,
                                border: `1px solid ${currentTheme.primary}30`,
                                color: currentTheme.primary
                            }}
                            onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => {
                                e.currentTarget.style.backgroundColor = `${currentTheme.primary}25`;
                                e.currentTarget.style.transform = 'translateX(4px)';
                                e.currentTarget.style.boxShadow = `0 4px 12px ${currentTheme.primary}20`;
                            }}
                            onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => {
                                e.currentTarget.style.backgroundColor = `${currentTheme.primary}15`;
                                e.currentTarget.style.transform = 'translateX(0)';
                                e.currentTarget.style.boxShadow = 'none';
                            }}
                        >
                            <span className="material-icons" style={{
                                transition: 'transform 0.3s ease',
                                fontSize: '24px',
                                marginRight: '12px'
                            }}>
                                {theme === 'light' ? 'dark_mode' : 'light_mode'}
                            </span>
                            {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
                        </button>

                        <button
                            onClick={handleLogout}
                            className="nav-button"
                            style={{
                                width: '100%',
                                justifyContent: 'flex-start',
                                padding: '1rem 1.25rem',
                                borderRadius: '12px',
                                transition: 'all 0.2s ease',
                                fontSize: '1rem',
                                backgroundColor: `${currentTheme.errorBackground}30`,
                                border: `1px solid rgba(244,67,54,0.3)`,
                                color: '#F44336',
                                marginTop: '1rem'
                            }}
                            onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => {
                                e.currentTarget.style.backgroundColor = `${currentTheme.errorBackground}50`;
                                e.currentTarget.style.transform = 'translateX(4px)';
                                e.currentTarget.style.boxShadow = '0 4px 12px rgba(244,67,54,0.2)';
                            }}
                            onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => {
                                e.currentTarget.style.backgroundColor = `${currentTheme.errorBackground}30`;
                                e.currentTarget.style.transform = 'translateX(0)';
                                e.currentTarget.style.boxShadow = 'none';
                            }}
                        >
                            <span className="material-icons" style={{
                                transition: 'transform 0.3s ease',
                                fontSize: '24px',
                                marginRight: '12px'
                            }}>
                                logout
                            </span>
                            Logout
                        </button>
                    </div>
                </div>

                <main style={{
                    padding: '2rem',
                    paddingTop: '3.5rem',
                    maxWidth: '1200px',
                    margin: '0 auto',
                    width: '100%',
                    boxSizing: 'border-box',
                    flex: 1
                }}>
                    {/* Server Header */}
                    <div style={{
                        marginBottom: '2.5rem',
                        paddingTop: '1rem'
                    }}>
                        <h1 style={{
                            fontSize: '1.75rem',
                            margin: '0 0 1.5rem 0',
                            display: 'flex',
                            alignItems: 'center',
                            color: currentTheme.text
                        }}>
                            <span className="material-icons" style={{
                                fontSize: '28px',
                                marginRight: '12px',
                                color: currentTheme.primary
                            }}>
                                vpn_lock
                            </span>
                            OpenVPN Server Management
                            {serverStatus !== 'unknown' && (
                                <div className={`status-indicator ${serverStatus}`} style={{
                                    marginTop: '4px',
                                    marginLeft: '12px',
                                    display: 'inline-flex',
                                    alignItems: 'center'
                                }}>
                                    <span className="material-icons" style={{
                                        fontSize: '12px',
                                        marginRight: '3px',
                                        verticalAlign: 'middle'
                                    }}>
                                        {serverStatus === 'running' ? 'circle' : 'stop_circle'}
                                    </span>
                                    {serverStatus === 'running' ? 'Running' : 'Stopped'}
                                </div>
                            )}
                        </h1>

                        <p style={{
                            margin: '0 0 1rem 0',
                            fontSize: '1rem',
                            opacity: 0.8,
                            maxWidth: '800px',
                            lineHeight: '1.5',
                            color: currentTheme.text
                        }}>
                            Configure and manage your OpenVPN server settings, monitor connections, and create client configurations.
                        </p>
                    </div>

                    {/* Loading Overlay */}
                    {loading && (
                        <div style={{
                            position: 'fixed',
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            backgroundColor: 'rgba(0, 0, 0, 0.7)',
                            backdropFilter: 'blur(4px)',
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            zIndex: 9999
                        }}>
                            <div style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: '1rem'
                            }}>
                                <div style={{
                                    width: '48px',
                                    height: '48px',
                                    border: `4px solid ${currentTheme.primary}30`,
                                    borderTop: `4px solid ${currentTheme.primary}`,
                                    borderRadius: '50%',
                                    animation: 'spin 1s linear infinite'
                                }} />
                                <div style={{ color: 'white', fontWeight: 500 }}>
                                    Processing...
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Server Actions Grid */}
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
                        gap: '1.5rem',
                        marginBottom: '2rem'
                    }}>
                        {/* Setup and Reset Container */}
                        <div style={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '0.5rem'
                        }}>
                            {/* Setup Button */}
                            <button
                                className="server-action-button setup"
                                onClick={() => handleServerOperation('setup')}
                                disabled={loading}
                                onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => {
                                    e.currentTarget.style.opacity = '0.8';
                                    e.currentTarget.style.transform = 'translateX(-4px)';
                                }}
                                onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => {
                                    e.currentTarget.style.opacity = '1';
                                    e.currentTarget.style.transform = 'translateX(0)';
                                }}
                                style={{
                                    height: '65px',
                                    padding: '0.75rem'
                                }}
                            >
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '12px'
                                }}>
                                    <span className="material-icons" style={{ fontSize: '28px', color: currentTheme.secondary }}>
                                        settings
                                    </span>
                                    <div>
                                        <div style={{ fontWeight: '500', fontSize: '1rem', textAlign: 'left' }}>
                                            Server Setup
                                        </div>
                                        <div style={{ fontSize: '0.75rem', opacity: 0.8, textAlign: 'left' }}>
                                            Configure OpenVPN settings
                                        </div>
                                    </div>
                                </div>
                            </button>

                            {/* Delete Server Button */}
                            <button
                                className="server-action-button"
                                onClick={() => setDeleteConfirmModalOpen(true)}
                                disabled={loading}
                                onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => {
                                    e.currentTarget.style.opacity = '0.8';
                                    e.currentTarget.style.transform = 'translateX(-4px)';
                                }}
                                onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => {
                                    e.currentTarget.style.opacity = '1';
                                    e.currentTarget.style.transform = 'translateX(0)';
                                }}
                                style={{
                                    height: '65px',
                                    padding: '0.75rem',
                                    borderColor: '#F4433660',
                                    backgroundColor: '#F4433610',
                                }}
                            >
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '12px'
                                }}>
                                    <span className="material-icons" style={{ fontSize: '28px', color: '#F44336' }}>
                                        delete_forever
                                    </span>
                                    <div>
                                        <div style={{ fontWeight: '500', fontSize: '1rem', textAlign: 'left' }}>
                                            Delete Configuration
                                        </div>
                                        <div style={{ fontSize: '0.75rem', opacity: 0.8, textAlign: 'left' }}>
                                            Reset server certificates
                                        </div>
                                    </div>
                                </div>
                            </button>
                        </div>

                        {/* Start/Stop Container */}
                        <div style={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '0.5rem'
                        }}>
                            {/* Start Button */}
                            <button
                                className="server-action-button start"
                                onClick={() => handleServerOperation('start')}
                                disabled={loading || serverStatus === 'running'}
                                onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => {
                                    e.currentTarget.style.opacity = '0.8';
                                    e.currentTarget.style.transform = 'translateX(-4px)';
                                }}
                                onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => {
                                    e.currentTarget.style.opacity = '1';
                                    e.currentTarget.style.transform = 'translateX(0)';
                                }}
                                style={{
                                    height: '65px',
                                    padding: '0.75rem'
                                }}
                            >
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '12px'
                                }}>
                                    <span className="material-icons" style={{ fontSize: '28px', color: currentTheme.primary }}>
                                        play_circle
                                    </span>
                                    <div>
                                        <div style={{ fontWeight: '500', fontSize: '1rem', textAlign: 'left' }}>
                                            Start Server
                                        </div>
                                        <div style={{ fontSize: '0.75rem', opacity: 0.8, textAlign: 'left' }}>
                                            Start the OpenVPN service
                                        </div>
                                    </div>
                                </div>
                            </button>

                            {/* Stop Button */}
                            <button
                                className="server-action-button stop"
                                onClick={() => handleServerOperation('stop')}
                                disabled={loading || serverStatus !== 'running'}
                                onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => {
                                    e.currentTarget.style.opacity = '0.8';
                                    e.currentTarget.style.transform = 'translateX(-4px)';
                                }}
                                onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => {
                                    e.currentTarget.style.opacity = '1';
                                    e.currentTarget.style.transform = 'translateX(0)';
                                }}
                                style={{
                                    height: '65px',
                                    padding: '0.75rem',
                                    borderColor: '#F4433660',
                                    backgroundColor: '#F4433610',
                                }}
                            >
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '12px'
                                }}>
                                    <span className="material-icons" style={{ fontSize: '28px', color: '#F44336' }}>
                                        stop_circle
                                    </span>
                                    <div>
                                        <div style={{ fontWeight: '500', fontSize: '1rem', textAlign: 'left' }}>
                                            Stop Server
                                        </div>
                                        <div style={{ fontSize: '0.75rem', opacity: 0.8, textAlign: 'left' }}>
                                            Stop the OpenVPN service
                                        </div>
                                    </div>
                                </div>
                            </button>
                        </div>

                        {/* Create Client Button */}
                        <button
                            className="server-action-button client"
                            onClick={() => setCreateClientModalOpen(true)}
                            disabled={loading}
                            onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => {
                                e.currentTarget.style.opacity = '0.8';
                                e.currentTarget.style.transform = 'translateX(-4px)';
                            }}
                            onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => {
                                e.currentTarget.style.opacity = '1';
                                e.currentTarget.style.transform = 'translateX(0)';
                            }}
                        >
                            <span className="material-icons" style={{ fontSize: '36px', color: '#FF9800' }}>
                                person_add
                            </span>
                            <div style={{ fontWeight: '500', fontSize: '1.1rem' }}>
                                Create New Client
                            </div>
                            <div style={{ fontSize: '0.85rem', opacity: 0.8, textAlign: 'center' }}>
                                Generate client configuration
                            </div>
                        </button>
                    </div>

                    {/* Second row for Edit button */}
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
                        gap: '1.5rem',
                        marginBottom: '2rem'
                    }}>
                        {/* Edit Server Button */}
                        <div style={{
                            position: 'relative',
                            width: '100%',
                            height: '100%'
                        }}>
                            <div
                                style={{
                                    position: 'absolute',
                                    top: '-40px',
                                    left: '50%',
                                    transform: 'translateX(-50%)',
                                    backgroundColor: 'rgba(0,0,0,0.8)',
                                    color: 'white',
                                    padding: '8px 12px',
                                    borderRadius: '6px',
                                    fontSize: '0.8rem',
                                    zIndex: '100',
                                    whiteSpace: 'nowrap',
                                    boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
                                    visibility: 'hidden',
                                    opacity: 0,
                                    transition: 'opacity 0.3s ease, visibility 0.3s ease',
                                    pointerEvents: 'none'
                                }}
                                className="tooltip-text"
                            >
                                Próximamente disponible
                                <div style={{
                                    position: 'absolute',
                                    bottom: '-6px',
                                    left: '50%',
                                    transform: 'translateX(-50%)',
                                    width: '0',
                                    height: '0',
                                    borderLeft: '6px solid transparent',
                                    borderRight: '6px solid transparent',
                                    borderTop: '6px solid rgba(0,0,0,0.8)'
                                }}></div>
                            </div>

                            <button
                                className="server-action-button edit"
                                disabled={true}
                                style={{
                                    position: 'relative',
                                    opacity: '0.6',
                                    cursor: 'not-allowed',
                                    width: '100%'
                                }}
                                onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => {
                                    // Mostrar tooltip usando CSS
                                    const parent = e.currentTarget.parentElement;
                                    if (parent) {
                                        const tooltip = parent.querySelector('.tooltip-text') as HTMLElement;
                                        if (tooltip) {
                                            tooltip.style.visibility = 'visible';
                                            tooltip.style.opacity = '1';
                                        }
                                    }
                                }}
                                onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => {
                                    // Ocultar tooltip
                                    const parent = e.currentTarget.parentElement;
                                    if (parent) {
                                        const tooltip = parent.querySelector('.tooltip-text') as HTMLElement;
                                        if (tooltip) {
                                            tooltip.style.visibility = 'hidden';
                                            tooltip.style.opacity = '0';
                                        }
                                    }
                                }}
                            >
                                <span className="material-icons" style={{ fontSize: '36px', color: '#9C27B0', opacity: '0.5' }}>
                                    edit
                                </span>
                                <div style={{ fontWeight: '500', fontSize: '1.1rem', color: '#666' }}>
                                    Edit Configuration
                                </div>
                                <div style={{ fontSize: '0.85rem', opacity: 0.8, textAlign: 'center', color: '#888' }}>
                                    Modify server configuration
                                </div>
                            </button>
                        </div>
                    </div>

                    {/* Server Status and Info Card */}
                    <div style={{
                        backgroundColor: currentTheme.cardBackground,
                        border: `1px solid ${currentTheme.border}`,
                        borderRadius: '12px',
                        padding: '1.5rem',
                        marginBottom: '2rem',
                        color: currentTheme.text
                    }}>
                        <h2 style={{
                            margin: '0 0 1.5rem 0',
                            fontSize: '1.3rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            color: currentTheme.text
                        }}>
                            <span className="material-icons" style={{ color: currentTheme.secondary }}>
                                info
                            </span>
                            Server Information
                        </h2>

                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                            gap: '1.5rem'
                        }}>
                            <div style={{
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '0.5rem'
                            }}>
                                <div style={{ opacity: 0.7, fontSize: '0.9rem', color: currentTheme.text }}>IP Address</div>
                                <div style={{ fontSize: '1.1rem', fontWeight: '500', color: currentTheme.text }}>{serverConfig.public_ip || "-"}</div>
                            </div>

                            <div style={{
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '0.5rem'
                            }}>
                                <div style={{ opacity: 0.7, fontSize: '0.9rem', color: currentTheme.text }}>Port</div>
                                <div style={{ fontSize: '1.1rem', fontWeight: '500', color: currentTheme.text }}>{serverConfig.openvpn_port ? `${serverConfig.openvpn_port} (${serverConfig.openvpn_proto.toUpperCase()})` : "-"}</div>
                            </div>

                            <div style={{
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '0.5rem'
                            }}>
                                <div style={{ opacity: 0.7, fontSize: '0.9rem', color: currentTheme.text }}>Protocol</div>
                                <div style={{ fontSize: '1.1rem', fontWeight: '500', color: currentTheme.text }}>{serverConfig.openvpn_proto ? serverConfig.openvpn_proto.toUpperCase() : "-"}</div>
                            </div>

                            <div style={{
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '0.5rem'
                            }}>
                                <div style={{ opacity: 0.7, fontSize: '0.9rem', color: currentTheme.text }}>VPN Network</div>
                                <div style={{ fontSize: '1.1rem', fontWeight: '500', color: currentTheme.text }}>{serverConfig.vpn_network || "-"}</div>
                            </div>

                            <div style={{
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '0.5rem'
                            }}>
                                <div style={{ opacity: 0.7, fontSize: '0.9rem', color: currentTheme.text }}>Netmask</div>
                                <div style={{ fontSize: '1.1rem', fontWeight: '500', color: currentTheme.text }}>{serverConfig.vpn_netmask || "-"}</div>
                            </div>

                            <div style={{
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '0.5rem'
                            }}>
                                <div style={{ opacity: 0.7, fontSize: '0.9rem', color: currentTheme.text }}>Encryption</div>
                                <div style={{ fontSize: '1.1rem', fontWeight: '500', color: currentTheme.text }}>{serverConfig.vpn_network ? "AES-256-GCM" : "-"}</div>
                            </div>
                        </div>
                    </div>

                    {/* Add clients list section after server info card */}
                    <div style={{
                        backgroundColor: `${currentTheme.cardBackground}`,
                        borderRadius: '12px',
                        border: `1px solid ${currentTheme.border}`,
                        padding: '1.5rem',
                        gridColumn: 'span 2',
                        height: 'auto',
                        transition: 'all 0.3s ease'
                    }}>
                        <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            marginBottom: '1.5rem'
                        }}>
                            <h2 style={{ margin: 0, fontSize: '1.4rem' }}>VPN Clients</h2>

                            {/* Client loading indicators */}
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '10px',
                                fontSize: '0.8rem',
                                opacity: 0.7
                            }}>
                                {clientsLoading && (
                                    <>
                                        <div style={{
                                            width: '16px',
                                            height: '16px',
                                            border: `2px solid ${currentTheme.borderLight}`,
                                            borderTop: `2px solid ${currentTheme.primary}`,
                                            borderRadius: '50%',
                                            animation: 'spin 1s linear infinite'
                                        }} />
                                        <span>Loading...</span>
                                    </>
                                )}
                            </div>
                        </div>

                        {clients.length > 0 ? (
                            <div style={{
                                display: 'grid',
                                gap: '1rem',
                                maxHeight: '400px',
                                overflowY: 'auto',
                                paddingRight: '10px'
                            }}>
                                {clients.map((client) => (
                                    <div
                                        key={client.name}
                                        style={{
                                            display: 'flex',
                                            justifyContent: 'space-between',
                                            alignItems: 'center',
                                            padding: '1rem',
                                            backgroundColor: `${currentTheme.background}`,
                                            borderRadius: '8px',
                                            border: `1px solid ${currentTheme.border}`
                                        }}
                                    >
                                        <div>
                                            <div style={{ fontWeight: '500', marginBottom: '0.25rem' }}>
                                                {client.name}
                                            </div>
                                            <div style={{ fontSize: '0.9rem', opacity: 0.8 }}>
                                                IP: {client.ip}
                                            </div>
                                            <div style={{ fontSize: '0.8rem', opacity: 0.6 }}>
                                                Created: {new Date(client.created_at).toLocaleString()}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div style={{
                                textAlign: 'center',
                                padding: '2rem',
                                opacity: 0.7
                            }}>
                                No clients created
                            </div>
                        )}
                    </div>
                </main>

                <Footer theme={currentTheme} />
            </div>

            {/* Create Client Modal */}
            {createClientModalOpen && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h2 style={{
                            margin: '0 0 1.5rem 0',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            fontSize: '1.3rem'
                        }}>
                            <span className="material-icons" style={{ color: '#FF9800' }}>
                                person_add
                            </span>
                            Create New Client
                        </h2>

                        {serverConfig.vpn_network && (
                            <div style={{
                                marginBottom: '1.5rem',
                                padding: '0.75rem',
                                backgroundColor: `${currentTheme.primary}15`,
                                borderRadius: '8px',
                                border: `1px solid ${currentTheme.primary}30`,
                                fontSize: '0.9rem',
                                color: currentTheme.text
                            }}>
                                <strong>Configured VPN Network:</strong> {serverConfig.vpn_network}/{serverConfig.vpn_netmask}
                            </div>
                        )}

                        <div style={{ marginBottom: '1.5rem' }}>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontSize: '0.9rem',
                                opacity: 0.8
                            }}>
                                Client Name
                            </label>
                            <input
                                type="text"
                                value={newClientName}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewClientName(e.target.value)}
                                placeholder="Enter client name (e.g. client1)"
                                style={{
                                    width: '100%',
                                    padding: '0.75rem',
                                    fontSize: '1rem',
                                    borderRadius: '8px',
                                    border: `1px solid ${currentTheme.border}`,
                                    backgroundColor: currentTheme.background,
                                    color: currentTheme.text,
                                    boxSizing: 'border-box'
                                }}
                            />
                            {clientError && (
                                <div style={{
                                    color: '#F44336',
                                    fontSize: '0.85rem',
                                    marginTop: '0.5rem'
                                }}>
                                    {clientError}
                                </div>
                            )}
                        </div>

                        <div style={{ marginBottom: '1.5rem' }}>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontSize: '0.9rem',
                                opacity: 0.8
                            }}>
                                Client IP
                            </label>
                            <input
                                type="text"
                                value={newClientIP}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewClientIP(e.target.value)}
                                placeholder="Enter client IP (e.g. 10.8.0.10)"
                                style={{
                                    width: '100%',
                                    padding: '0.75rem',
                                    fontSize: '1rem',
                                    borderRadius: '8px',
                                    border: `1px solid ${currentTheme.border}`,
                                    backgroundColor: currentTheme.background,
                                    color: currentTheme.text,
                                    boxSizing: 'border-box'
                                }}
                            />
                        </div>

                        <div style={{
                            display: 'flex',
                            justifyContent: 'flex-end',
                            gap: '1rem',
                            marginTop: '1.5rem'
                        }}>
                            <button
                                onClick={() => {
                                    setCreateClientModalOpen(false);
                                    setClientError(null);
                                }}
                                style={{
                                    padding: '0.75rem 1.25rem',
                                    borderRadius: '8px',
                                    border: `1px solid ${currentTheme.border}`,
                                    backgroundColor: 'transparent',
                                    color: currentTheme.text,
                                    fontSize: '0.95rem',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s ease'
                                }}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleCreateClient}
                                disabled={clientCreating}
                                style={{
                                    padding: '0.75rem 1.25rem',
                                    borderRadius: '8px',
                                    border: 'none',
                                    backgroundColor: '#FF9800',
                                    color: 'white',
                                    fontSize: '0.95rem',
                                    cursor: clientCreating ? 'not-allowed' : 'pointer',
                                    transition: 'all 0.2s ease',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                    opacity: clientCreating ? 0.7 : 1
                                }}
                            >
                                {clientCreating && (
                                    <div style={{
                                        width: '18px',
                                        height: '18px',
                                        border: '2px solid rgba(255,255,255,0.3)',
                                        borderTop: '2px solid white',
                                        borderRadius: '50%',
                                        animation: 'spin 1s linear infinite'
                                    }} />
                                )}
                                {clientCreating ? 'Creating...' : 'Create Client'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Setup Server Modal */}
            {setupModalOpen && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h2 style={{
                            margin: '0 0 1.5rem 0',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            fontSize: '1.3rem'
                        }}>
                            <span className="material-icons" style={{ color: currentTheme.secondary }}>
                                settings
                            </span>
                            OpenVPN Server Setup
                        </h2>

                        <div style={{ marginBottom: '1.5rem' }}>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontSize: '0.9rem',
                                opacity: 0.8
                            }}>
                                VPN Network
                            </label>
                            <input
                                type="text"
                                value={setupVpnNetwork}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSetupVpnNetwork(e.target.value)}
                                placeholder="Enter VPN network (e.g. 10.8.0.0)"
                                style={{
                                    width: '100%',
                                    padding: '0.75rem',
                                    fontSize: '1rem',
                                    borderRadius: '8px',
                                    border: `1px solid ${currentTheme.border}`,
                                    backgroundColor: currentTheme.background,
                                    color: currentTheme.text,
                                    boxSizing: 'border-box'
                                }}
                            />
                        </div>

                        <div style={{ marginBottom: '1.5rem' }}>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontSize: '0.9rem',
                                opacity: 0.8
                            }}>
                                VPN Netmask
                            </label>
                            <input
                                type="text"
                                value={setupVpnNetmask}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSetupVpnNetmask(e.target.value)}
                                placeholder="Enter VPN netmask (e.g. 255.255.255.0)"
                                style={{
                                    width: '100%',
                                    padding: '0.75rem',
                                    fontSize: '1rem',
                                    borderRadius: '8px',
                                    border: `1px solid ${currentTheme.border}`,
                                    backgroundColor: currentTheme.background,
                                    color: currentTheme.text,
                                    boxSizing: 'border-box'
                                }}
                            />
                        </div>

                        <div style={{ marginBottom: '1.5rem' }}>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontSize: '0.9rem',
                                opacity: 0.8
                            }}>
                                OpenVPN Port
                            </label>
                            <input
                                type="text"
                                value={setupOpenvpnPort}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSetupOpenvpnPort(e.target.value)}
                                placeholder="Enter port (e.g. 1194)"
                                style={{
                                    width: '100%',
                                    padding: '0.75rem',
                                    fontSize: '1rem',
                                    borderRadius: '8px',
                                    border: `1px solid ${currentTheme.border}`,
                                    backgroundColor: currentTheme.background,
                                    color: currentTheme.text,
                                    boxSizing: 'border-box'
                                }}
                            />
                        </div>

                        <div style={{ marginBottom: '1.5rem' }}>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontSize: '0.9rem',
                                opacity: 0.8
                            }}>
                                OpenVPN Protocol
                            </label>
                            <select
                                value={setupOpenvpnProto}
                                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSetupOpenvpnProto(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '0.75rem',
                                    fontSize: '1rem',
                                    borderRadius: '8px',
                                    border: `1px solid ${currentTheme.border}`,
                                    backgroundColor: currentTheme.background,
                                    color: currentTheme.text,
                                    boxSizing: 'border-box'
                                }}
                            >
                                <option value="udp">UDP</option>
                                <option value="tcp">TCP</option>
                            </select>
                        </div>

                        <div style={{ marginBottom: '1.5rem' }}>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontSize: '0.9rem',
                                opacity: 0.8
                            }}>
                                Public IP / Domain
                            </label>
                            <input
                                type="text"
                                value={setupPublicIp}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSetupPublicIp(e.target.value)}
                                placeholder="Enter public IP or domain (e.g. vpn.example.com)"
                                style={{
                                    width: '100%',
                                    padding: '0.75rem',
                                    fontSize: '1rem',
                                    borderRadius: '8px',
                                    border: `1px solid ${currentTheme.border}`,
                                    backgroundColor: currentTheme.background,
                                    color: currentTheme.text,
                                    boxSizing: 'border-box'
                                }}
                            />
                        </div>

                        {setupError && (
                            <div style={{
                                color: '#F44336',
                                fontSize: '0.85rem',
                                marginTop: '0.5rem',
                                marginBottom: '1rem',
                                padding: '0.75rem',
                                backgroundColor: `${currentTheme.errorBackground}50`,
                                borderRadius: '4px',
                                border: '1px solid rgba(244,67,54,0.3)'
                            }}>
                                {setupError}
                            </div>
                        )}

                        <div style={{
                            display: 'flex',
                            justifyContent: 'flex-end',
                            gap: '1rem',
                            marginTop: '1.5rem'
                        }}>
                            <button
                                onClick={() => {
                                    setSetupModalOpen(false);
                                    resetSetupForm();
                                }}
                                style={{
                                    padding: '0.75rem 1.25rem',
                                    borderRadius: '8px',
                                    border: `1px solid ${currentTheme.border}`,
                                    backgroundColor: 'transparent',
                                    color: currentTheme.text,
                                    fontSize: '0.95rem',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s ease'
                                }}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSetupSubmit}
                                disabled={setupProcessing}
                                style={{
                                    padding: '0.75rem 1.25rem',
                                    borderRadius: '8px',
                                    border: 'none',
                                    backgroundColor: currentTheme.secondary,
                                    color: 'white',
                                    fontSize: '0.95rem',
                                    cursor: setupProcessing ? 'not-allowed' : 'pointer',
                                    transition: 'all 0.2s ease',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                    opacity: setupProcessing ? 0.7 : 1
                                }}
                            >
                                {setupProcessing && (
                                    <div style={{
                                        width: '18px',
                                        height: '18px',
                                        border: '2px solid rgba(255,255,255,0.3)',
                                        borderTop: '2px solid white',
                                        borderRadius: '50%',
                                        animation: 'spin 1s linear infinite'
                                    }} />
                                )}
                                {setupProcessing ? 'Setting up...' : 'Configure Server'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Setup Confirmation Modal */}
            {setupConfirmModalOpen && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h2 style={{
                            margin: '0 0 1rem 0',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            fontSize: '1.3rem',
                            color: '#F44336'
                        }}>
                            <span className="material-icons" style={{ color: '#F44336' }}>
                                warning
                            </span>
                            Warning: Existing Configuration
                        </h2>

                        <div style={{
                            backgroundColor: `${currentTheme.errorBackground}50`,
                            border: '1px solid rgba(244,67,54,0.3)',
                            borderRadius: '8px',
                            padding: '1rem',
                            marginBottom: '1.5rem'
                        }}>
                            <p style={{
                                margin: '0 0 1rem 0',
                                fontSize: '1rem',
                                lineHeight: '1.5'
                            }}>
                                <strong>The server already has an existing configuration with certificates.</strong>
                            </p>
                            <p style={{
                                margin: '0 0 1rem 0',
                                fontSize: '0.95rem',
                                lineHeight: '1.5'
                            }}>
                                Proceeding will:
                            </p>
                            <ul style={{
                                margin: '0 0 1rem 0',
                                paddingLeft: '1.5rem',
                                fontSize: '0.95rem',
                                lineHeight: '1.5'
                            }}>
                                <li>Delete ALL existing certificates</li>
                                <li>Remove ALL client configurations</li>
                                <li>Create a new server configuration</li>
                                <li>Require new client certificates to be generated</li>
                            </ul>
                            <p style={{
                                margin: '0',
                                fontSize: '0.95rem',
                                fontWeight: 'bold',
                                lineHeight: '1.5'
                            }}>
                                This action cannot be undone. All clients will lose connection to the VPN server.
                            </p>
                        </div>

                        <div style={{
                            display: 'flex',
                            justifyContent: 'flex-end',
                            gap: '1rem',
                            marginTop: '1.5rem'
                        }}>
                            <button
                                onClick={() => {
                                    setSetupConfirmModalOpen(false);
                                }}
                                style={{
                                    padding: '0.75rem 1.25rem',
                                    borderRadius: '8px',
                                    border: `1px solid ${currentTheme.border}`,
                                    backgroundColor: 'transparent',
                                    color: currentTheme.text,
                                    fontSize: '0.95rem',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s ease'
                                }}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleConfirmSetup}
                                style={{
                                    padding: '0.75rem 1.25rem',
                                    borderRadius: '8px',
                                    border: 'none',
                                    backgroundColor: '#F44336',
                                    color: 'white',
                                    fontSize: '0.95rem',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s ease',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem'
                                }}
                            >
                                Proceed & Reset Server
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Delete Configuration Confirmation Modal */}
            {deleteConfirmModalOpen && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h2 style={{
                            margin: '0 0 1rem 0',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            fontSize: '1.3rem',
                            color: '#F44336'
                        }}>
                            <span className="material-icons" style={{ color: '#F44336' }}>
                                warning
                            </span>
                            Warning: Delete Server Configuration
                        </h2>

                        <div style={{
                            backgroundColor: `${currentTheme.errorBackground}50`,
                            border: '1px solid rgba(244,67,54,0.3)',
                            borderRadius: '8px',
                            padding: '1rem',
                            marginBottom: '1.5rem'
                        }}>
                            <p style={{
                                margin: '0 0 1rem 0',
                                fontSize: '1rem',
                                lineHeight: '1.5'
                            }}>
                                <strong>This action will permanently delete all server configuration.</strong>
                            </p>
                            <p style={{
                                margin: '0 0 1rem 0',
                                fontSize: '0.95rem',
                                lineHeight: '1.5'
                            }}>
                                The following data will be deleted:
                            </p>
                            <ul style={{
                                margin: '0 0 1rem 0',
                                paddingLeft: '1.5rem',
                                fontSize: '0.95rem',
                                lineHeight: '1.5'
                            }}>
                                <li>All server certificates and keys</li>
                                <li>All client configurations and certificates</li>
                                <li>OpenVPN server configuration</li>
                                <li>All connection profiles</li>
                            </ul>
                            <p style={{
                                margin: '0',
                                fontSize: '0.95rem',
                                fontWeight: 'bold',
                                lineHeight: '1.5'
                            }}>
                                This action cannot be undone. You will need to reconfigure the server and generate new client certificates.
                            </p>
                        </div>

                        {deleteError && (
                            <div style={{
                                color: '#F44336',
                                fontSize: '0.85rem',
                                marginTop: '0.5rem',
                                marginBottom: '1rem',
                                padding: '0.75rem',
                                backgroundColor: `${currentTheme.errorBackground}50`,
                                borderRadius: '4px',
                                border: '1px solid rgba(244,67,54,0.3)'
                            }}>
                                {deleteError}
                            </div>
                        )}

                        <div style={{
                            display: 'flex',
                            justifyContent: 'flex-end',
                            gap: '1rem',
                            marginTop: '1.5rem'
                        }}>
                            <button
                                onClick={() => {
                                    setDeleteConfirmModalOpen(false);
                                    setDeleteError(null);
                                }}
                                style={{
                                    padding: '0.75rem 1.25rem',
                                    borderRadius: '8px',
                                    border: `1px solid ${currentTheme.border}`,
                                    backgroundColor: 'transparent',
                                    color: currentTheme.text,
                                    fontSize: '0.95rem',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s ease'
                                }}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleDeleteConfiguration}
                                disabled={deleteProcessing}
                                style={{
                                    padding: '0.75rem 1.25rem',
                                    borderRadius: '8px',
                                    border: 'none',
                                    backgroundColor: '#F44336',
                                    color: 'white',
                                    fontSize: '0.95rem',
                                    cursor: deleteProcessing ? 'not-allowed' : 'pointer',
                                    transition: 'all 0.2s ease',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                    opacity: deleteProcessing ? 0.7 : 1
                                }}
                            >
                                {deleteProcessing && (
                                    <div style={{
                                        width: '18px',
                                        height: '18px',
                                        border: '2px solid rgba(255,255,255,0.3)',
                                        borderTop: '2px solid white',
                                        borderRadius: '50%',
                                        animation: 'spin 1s linear infinite'
                                    }} />
                                )}
                                {deleteProcessing ? 'Deleting...' : 'Delete All Server Data'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Delete Client Confirmation Modal */}
            {/* Modal removido según se solicitó */}
        </>
    );
}
