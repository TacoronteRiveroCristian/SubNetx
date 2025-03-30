/**
 * Server Management page component
 * Allows admin users to control and configure the OpenVPN server
 */
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import BackgroundEffect from '../components/BackgroundEffect';
import Footer from '../components/Footer';
import Logo from '../components/Logo';

// Define theme object
const themes = {
  light: {
    background: '#ffffff',
    text: '#333333',
    primary: '#4CAF50',
    secondary: '#2196F3',
    border: '#dddddd',
    tableHeader: '#f2f2f2',
    tableRow: '#ffffff',
    tableRowHover: '#f5f5f5',
    cardBackground: '#f9f9f9',
    errorBackground: '#FFEBEE',
    statusIndicator: '#E3F2FD',
    navbar: '#ffffff',
    buttonHover: '#f0f0f0',
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
  },
};

export default function ServerManagement() {
  // Initialize router for navigation
  const router = useRouter();

  // State variables
  const [loading, setLoading] = useState(false);
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [isHamburgerOpen, setIsHamburgerOpen] = useState(false);
  const [serverStatus, setServerStatus] = useState<'running' | 'stopped' | 'unknown'>('unknown');
  const [createClientModalOpen, setCreateClientModalOpen] = useState(false);
  const [newClientName, setNewClientName] = useState('');
  const [clientCreating, setClientCreating] = useState(false);
  const [clientError, setClientError] = useState<string | null>(null);

  // Get current theme
  const currentTheme = themes[theme];

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

      // Mock server status check - in real implementation this would fetch from the API
      setServerStatus('stopped');
    };

    checkAuth();
  }, [router]);

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

  // Mock functions for server operations
  const handleServerOperation = (operation: 'setup' | 'start' | 'stop' | 'edit') => {
    setLoading(true);

    // Simulate API call with timeout
    setTimeout(() => {
      if (operation === 'start') {
        setServerStatus('running');
      } else if (operation === 'stop') {
        setServerStatus('stopped');
      }

      setLoading(false);
    }, 1500);
  };

  // Function to create a new client
  const handleCreateClient = () => {
    if (!newClientName.trim()) {
      setClientError('Client name is required');
      return;
    }

    setClientCreating(true);
    setClientError(null);

    // Simulate API call with timeout
    setTimeout(() => {
      // Mock client creation success
      setClientCreating(false);
      setCreateClientModalOpen(false);
      setNewClientName('');

      // In real implementation, this would handle download of client configuration
    }, 1500);
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
          }
          .content-container {
            position: relative;
            z-index: 1;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            background: transparent;
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
            display: inline-flex;
            align-items: center;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 500;
            margin-left: 10px;
          }
          .status-indicator.running {
            background-color: ${currentTheme.primary}30;
            color: ${currentTheme.primary};
          }
          .status-indicator.stopped {
            background-color: #F4433620;
            color: #F44336;
            font-size: 0.8rem;
            padding: 4px 10px;
            opacity: 0.8;
          }
          .status-indicator.unknown {
            background-color: #78909C30;
            color: #78909C;
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
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = '0.8';
                e.currentTarget.style.transform = 'translateX(-4px)';
              }}
              onMouseLeave={(e) => {
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
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = `${currentTheme.primary}25`;
                e.currentTarget.style.transform = 'translateX(4px)';
                e.currentTarget.style.boxShadow = `0 4px 12px ${currentTheme.primary}20`;
              }}
              onMouseLeave={(e) => {
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
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = `${currentTheme.secondary}25`;
                e.currentTarget.style.transform = 'translateX(4px)';
                e.currentTarget.style.boxShadow = `0 4px 12px ${currentTheme.secondary}20`;
              }}
              onMouseLeave={(e) => {
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
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = `${currentTheme.secondary}25`;
                e.currentTarget.style.transform = 'translateX(4px)';
                e.currentTarget.style.boxShadow = `0 4px 12px ${currentTheme.secondary}20`;
              }}
              onMouseLeave={(e) => {
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
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = `${currentTheme.primary}25`;
                e.currentTarget.style.transform = 'translateX(4px)';
                e.currentTarget.style.boxShadow = `0 4px 12px ${currentTheme.primary}20`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = `${currentTheme.primary}15`;
                e.currentTarget.style.transform = 'translateX(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <span className="material-icons" style={{
                transition: 'transform 0.4s ease, opacity 0.3s ease',
                transform: theme === 'light' ? 'translateY(0)' : 'translateY(-2px) rotate(180deg)',
                marginRight: '12px',
                fontSize: '24px'
              }}>
                {theme === 'light' ? 'light_mode' : 'dark_mode'}
              </span>
              {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
            </button>
          </div>

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
              border: `1px solid ${currentTheme.errorBackground}50`,
              color: '#F44336',
              marginTop: '1rem'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = `${currentTheme.errorBackground}50`;
              e.currentTarget.style.transform = 'translateX(4px)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(244,67,54,0.2)';
            }}
            onMouseLeave={(e) => {
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

        {/* Main Content */}
        <main style={{
          padding: '2rem',
          flex: 1,
          overflowY: 'auto',
          width: '100%',
          boxSizing: 'border-box',
          position: 'relative',
          zIndex: 1,
          color: currentTheme.text
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '2rem',
            flexWrap: 'wrap',
            gap: '1rem'
          }}>
            <h1 style={{
              margin: 0,
              display: 'flex',
              alignItems: 'flex-end',
              fontSize: '1.75rem'
            }}>
              <span className="material-icons" style={{
                marginRight: '12px',
                fontSize: '28px',
                color: currentTheme.secondary,
                marginBottom: '4px'
              }}>
                vpn_lock
              </span>
              <span style={{ lineHeight: 1 }}>OpenVPN Server Management</span>
              <div className={`status-indicator ${serverStatus}`} style={{
                marginBottom: '10px',
                marginLeft: '12px',
                transform: 'translateY(10px)'
              }}>
                <span className="material-icons" style={{
                  fontSize: serverStatus === 'stopped' ? '16px' : '20px',
                  marginRight: '8px'
                }}>
                  {serverStatus === 'running' ? 'check_circle' : serverStatus === 'stopped' ? 'cancel' : 'help'}
                </span>
                {serverStatus === 'running' ? 'Running' : serverStatus === 'stopped' ? 'Stopped' : 'Unknown'}
              </div>
            </h1>
          </div>

          {/* Server Actions Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
            gap: '1.5rem',
            marginBottom: '2rem'
          }}>
            {/* Setup Button */}
            <button
              className="server-action-button setup"
              onClick={() => handleServerOperation('setup')}
              disabled={loading}
            >
              <span className="material-icons" style={{ fontSize: '36px', color: currentTheme.secondary }}>
                settings
              </span>
              <div style={{ fontWeight: '500', fontSize: '1.1rem' }}>
                Server Setup
              </div>
              <div style={{ fontSize: '0.85rem', opacity: 0.8, textAlign: 'center' }}>
                Configure OpenVPN server settings
              </div>
            </button>

            {/* Start Button */}
            <button
              className="server-action-button start"
              onClick={() => handleServerOperation('start')}
              disabled={loading || serverStatus === 'running'}
            >
              <span className="material-icons" style={{ fontSize: '36px', color: currentTheme.primary }}>
                play_circle
              </span>
              <div style={{ fontWeight: '500', fontSize: '1.1rem' }}>
                Start Server
              </div>
              <div style={{ fontSize: '0.85rem', opacity: 0.8, textAlign: 'center' }}>
                Start the OpenVPN service
              </div>
            </button>

            {/* Stop Button */}
            <button
              className="server-action-button stop"
              onClick={() => handleServerOperation('stop')}
              disabled={loading || serverStatus !== 'running'}
            >
              <span className="material-icons" style={{ fontSize: '36px', color: '#F44336' }}>
                stop_circle
              </span>
              <div style={{ fontWeight: '500', fontSize: '1.1rem' }}>
                Stop Server
              </div>
              <div style={{ fontSize: '0.85rem', opacity: 0.8, textAlign: 'center' }}>
                Stop the OpenVPN service
              </div>
            </button>

            {/* Create Client Button */}
            <button
              className="server-action-button client"
              onClick={() => setCreateClientModalOpen(true)}
              disabled={loading}
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

            {/* Edit Server Button */}
            <button
              className="server-action-button edit"
              onClick={() => handleServerOperation('edit')}
              disabled={loading}
            >
              <span className="material-icons" style={{ fontSize: '36px', color: '#9C27B0' }}>
                edit
              </span>
              <div style={{ fontWeight: '500', fontSize: '1.1rem' }}>
                Edit Configuration
              </div>
              <div style={{ fontSize: '0.85rem', opacity: 0.8, textAlign: 'center' }}>
                Modify server configuration
              </div>
            </button>
          </div>

          {/* Server Status and Info Card */}
          <div style={{
            backgroundColor: currentTheme.cardBackground,
            borderRadius: '12px',
            padding: '1.5rem',
            marginBottom: '2rem',
            border: `1px solid ${currentTheme.border}`
          }}>
            <h2 style={{
              margin: '0 0 1rem 0',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '1.3rem'
            }}>
              <span className="material-icons" style={{ color: currentTheme.primary }}>
                info
              </span>
              Server Information
            </h2>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
              gap: '1.5rem'
            }}>
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.5rem'
              }}>
                <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Status</div>
                <div style={{ fontSize: '1.1rem', fontWeight: '500' }}>
                  {serverStatus === 'running' ? 'Running' : serverStatus === 'stopped' ? 'Stopped' : 'Unknown'}
                </div>
              </div>

              <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.5rem'
              }}>
                <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>IP Address</div>
                <div style={{ fontSize: '1.1rem', fontWeight: '500' }}>192.168.1.1</div>
              </div>

              <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.5rem'
              }}>
                <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Port</div>
                <div style={{ fontSize: '1.1rem', fontWeight: '500' }}>1194 (UDP)</div>
              </div>

              <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.5rem'
              }}>
                <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Protocol</div>
                <div style={{ fontSize: '1.1rem', fontWeight: '500' }}>UDP</div>
              </div>

              <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.5rem'
              }}>
                <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Encryption</div>
                <div style={{ fontSize: '1.1rem', fontWeight: '500' }}>AES-256-GCM</div>
              </div>

              <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.5rem'
              }}>
                <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>Connected Clients</div>
                <div style={{ fontSize: '1.1rem', fontWeight: '500' }}>
                  {serverStatus === 'running' ? 3 : 0}
                </div>
              </div>
            </div>
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
                onChange={(e) => setNewClientName(e.target.value)}
                placeholder="Enter client name"
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

            <div style={{
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '1rem',
              marginTop: '1rem'
            }}>
              <button
                onClick={() => {
                  setCreateClientModalOpen(false);
                  setNewClientName('');
                  setClientError(null);
                }}
                style={{
                  padding: '0.75rem 1.25rem',
                  borderRadius: '8px',
                  border: `1px solid ${currentTheme.border}`,
                  backgroundColor: 'transparent',
                  color: currentTheme.text,
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  transition: 'all 0.2s ease'
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleCreateClient}
                disabled={clientCreating || !newClientName.trim()}
                style={{
                  padding: '0.75rem 1.25rem',
                  borderRadius: '8px',
                  border: 'none',
                  backgroundColor: '#FF9800',
                  color: 'white',
                  cursor: clientCreating || !newClientName.trim() ? 'not-allowed' : 'pointer',
                  fontSize: '0.9rem',
                  opacity: clientCreating || !newClientName.trim() ? 0.7 : 1,
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                {clientCreating ? (
                  <>
                    <span className="material-icons" style={{
                      fontSize: '20px',
                      animation: 'spin 1s linear infinite'
                    }}>
                      hourglass_top
                    </span>
                    Creating...
                  </>
                ) : (
                  <>
                    <span className="material-icons" style={{ fontSize: '20px' }}>
                      check
                    </span>
                    Create Client
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
