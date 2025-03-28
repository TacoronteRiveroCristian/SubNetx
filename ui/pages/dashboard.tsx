/**
 * Dashboard page component for authenticated users
 * Contains the main application functionality
 */
// pages/dashboard.tsx
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useEffect, useRef, useState } from 'react';
import BackgroundEffect from '../components/BackgroundEffect'; // Import BackgroundEffect component
import Logo from '../components/Logo';

// Define the Target interface to type our data
interface Target {
  id: number;
  target: string;
  description: string | null;
  added_at: string;
}

// Define the TargetLatest interface for the latest status data
interface TargetLatest {
  id: number;
  target_id: number;
  timestamp: string;
  status: string;
  connection_quality: string;
  packet_loss_percent: number;
  min_rtt: number;
  avg_rtt: number;
  max_rtt: number;
  mdev_rtt: number;
  packets_transmitted: number;
  packets_received: number;
  icmp_details: {
    sequence: number;
    response_time_ms: number;
  }[];
  tls_info: {
    cert_expiry: string | null;
    issuer: string | null;
    subject: string | null;
    version: string | null;
    cipher: string | null;
  };
}

// Combined interface for display
interface TargetWithStatus {
  target: Target;
  latestStatus: TargetLatest | null;
}

// Theme configuration
interface Theme {
  background: string;
  text: string;
  primary: string;
  secondary: string;
  border: string;
  tableHeader: string;
  tableRow: string;
  tableRowHover: string;
  cardBackground: string;
  errorBackground: string;
  statusIndicator: string;
  navbar: string;
  buttonHover: string;
}

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

export default function Dashboard() {
  // Router for navigation
  const router = useRouter();

  // Check authentication on mount
  useEffect(() => {
    // If not authenticated, redirect to login
    if (localStorage.getItem('isAuthenticated') !== 'true') {
      router.push('/login');
    }
  }, [router]);

  // State to store the targets fetched from the API
  const [targets, setTargets] = useState<Target[]>([]);
  // State to store the latest status for each target
  const [latestStatuses, setLatestStatuses] = useState<TargetLatest[]>([]);
  // State to track loading status
  const [loading, setLoading] = useState(false);
  // State to track error messages
  const [error, setError] = useState<string | null>(null);
  // State to track if real-time monitoring is active
  const [isMonitoring, setIsMonitoring] = useState(false);
  // State to track the current theme
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  // State to track if settings panel is open
  const [showSettings, setShowSettings] = useState(false);
  // State to track refresh interval
  const [refreshInterval, setRefreshInterval] = useState(10);
  // State to track when data is being updated
  const [isUpdating, setIsUpdating] = useState(false);
  // State to track if hamburger menu is open
  const [isHamburgerOpen, setIsHamburgerOpen] = useState(false);
  // State to track if menu is in closing animation
  const [isMenuClosing, setIsMenuClosing] = useState(false);
  // Ref to store the interval ID for cleanup
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  // Add these new states at the top with other states
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: 'ascending' | 'descending';
  } | null>(null);
  const [filterText, setFilterText] = useState('');

  // Ensure theme is set to dark on initial render
  useEffect(() => {
    // Force dark theme on initial load
    setTheme('dark');
  }, []);

  // Function to fetch targets from the API
  const fetchTargets = async () => {
    // Reset states before fetching
    setLoading(true);
    setError(null);

    try {
      // Make API request to fetch targets using the proxy endpoint to avoid CORS issues
      const response = await fetch('/api/targets', {
        headers: {
          'accept': 'application/json'
        }
      });

      // Check if the request was successful
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      // Parse the JSON response
      const data = await response.json();
      // Update the targets state with the fetched data
      setTargets(data);

      // Fetch latest status data after getting targets
      await fetchLatestStatus();
    } catch (err) {
      // Handle any errors that occurred during the fetch
      setError(err instanceof Error ? err.message : 'An error occurred while fetching targets');
      console.error('Error fetching targets:', err);
    } finally {
      // Set loading to false regardless of success or failure
      setLoading(false);
    }
  };

  // Function to fetch latest status for all targets
  const fetchLatestStatus = async () => {
    try {
      setIsUpdating(true); // Set updating state to true
      // Make API request to fetch latest status data
      const response = await fetch('/api/targets/latest', {
        headers: {
          'accept': 'application/json'
        }
      });

      // Check if the request was successful
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      // Parse the JSON response
      const data = await response.json();
      // Update the latestStatuses state with the fetched data
      setLatestStatuses(data);
    } catch (err) {
      console.error('Error fetching latest status:', err);
      // We don't set the error state here to avoid interfering with the targets display
    } finally {
      // Reset updating state after a short delay
      setTimeout(() => setIsUpdating(false), 500);
    }
  };

  // Function to toggle real-time monitoring
  const toggleMonitoring = () => {
    if (isMonitoring) {
      // Stop monitoring
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setIsMonitoring(false);
    } else {
      // Start monitoring - fetch targets first, then start the interval
      fetchTargets().then(() => {
        // Set up interval to fetch latest status every refreshInterval seconds
        intervalRef.current = setInterval(fetchLatestStatus, refreshInterval * 1000);
        setIsMonitoring(true);
      });
    }
  };

  // Function to update refresh interval
  const updateRefreshInterval = (newInterval: number) => {
    setRefreshInterval(newInterval);
    if (isMonitoring && intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = setInterval(fetchLatestStatus, newInterval * 1000);
    }
  };

  // Function to toggle theme
  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'light' ? 'dark' : 'light');
  };

  // Clean up interval on component unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  // Combine targets with their latest status
  const targetsWithStatus: TargetWithStatus[] = targets.map(target => {
    const latestStatus = latestStatuses.find(status => status.target_id === target.id) || null;
    return {
      target,
      latestStatus
    };
  });

  // Get status color based on connection quality
  const getStatusColor = (quality: string) => {
    switch (quality) {
      case 'excellent':
        return '#4CAF50'; // Green
      case 'good':
        return '#8BC34A'; // Light Green
      case 'fair':
        return '#FFC107'; // Amber
      case 'poor':
        return '#FF9800'; // Orange
      case 'critical':
        return '#F44336'; // Red
      case 'none':
      default:
        return '#9E9E9E'; // Grey
    }
  };

  // Format date string to more readable format
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  // Get current theme colors
  const currentTheme = themes[theme];

  // Añadir esta función antes del return del componente Dashboard
  const getComparableValue = (item: TargetWithStatus, key: string) => {
    const { target, latestStatus } = item;
    switch (key) {
      case 'id':
        return target.id;
      case 'target':
        return target.target.toLowerCase();
      case 'timestamp':
        return latestStatus ? new Date(latestStatus.timestamp).getTime() : 0;
      case 'status':
        return latestStatus?.status || '';
      case 'quality':
        return latestStatus?.connection_quality || '';
      case 'packetLoss':
        return latestStatus?.packet_loss_percent || 0;
      case 'avgRtt':
        return latestStatus?.avg_rtt || 0;
      default:
        return '';
    }
  };

  // Modificar la función sortData existente
  const sortData = (data: TargetWithStatus[]) => {
    if (!sortConfig) return data;

    return [...data].sort((a, b) => {
      const aValue = getComparableValue(a, sortConfig.key);
      const bValue = getComparableValue(b, sortConfig.key);

      if (aValue < bValue) {
        return sortConfig.direction === 'ascending' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'ascending' ? 1 : -1;
      }
      return 0;
    });
  };

  // Add this filter function
  const filterData = (data: TargetWithStatus[]) => {
    if (!filterText) return data;
    const searchTerm = filterText.toLowerCase();

    return data.filter(item =>
      item.target.target.toLowerCase().includes(searchTerm) ||
      item.target.description?.toLowerCase().includes(searchTerm) ||
      item.latestStatus?.status.toLowerCase().includes(searchTerm) ||
      item.latestStatus?.connection_quality.toLowerCase().includes(searchTerm)
    );
  };

  // Add this function to handle sort
  const requestSort = (key: string) => {
    let direction: 'ascending' | 'descending' = 'ascending';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };

  // Add these helper functions before the return statement
  const calculateSystemHealth = (targets: TargetWithStatus[]) => {
    if (targets.length === 0) return 0;
    const onlineTargets = targets.filter(t => t.latestStatus?.status === 'online').length;
    return Math.round((onlineTargets / targets.length) * 100);
  };

  const calculateAverageRTT = (targets: TargetWithStatus[]) => {
    const validRTTs = targets
      .filter(t => t.latestStatus?.avg_rtt !== undefined && t.latestStatus.status === 'online')
      .map(t => t.latestStatus!.avg_rtt);
    if (validRTTs.length === 0) return 0;
    return Math.round(validRTTs.reduce((a, b) => a + b, 0) / validRTTs.length);
  };

  const getConnectionQualityDistribution = (targets: TargetWithStatus[]) => {
    const distribution = {
      Excellent: 0,
      Good: 0,
      Fair: 0,
      Poor: 0,
      None: 0
    };
    targets.forEach(t => {
      const quality = t.latestStatus?.connection_quality.toLowerCase() || 'none';
      if (quality === 'excellent') distribution.Excellent++;
      else if (quality === 'good') distribution.Good++;
      else if (quality === 'fair') distribution.Fair++;
      else if (quality === 'poor') distribution.Poor++;
      else distribution.None++;
    });
    return distribution;
  };

  // Function to handle logout - redirects to login page
  const handleLogout = () => {
    // Clear authentication in localStorage
    localStorage.removeItem('isAuthenticated');
    // Redirect to login page
    router.push('/login');
  };

  // Function to handle menu close with animation
  const handleMenuClose = () => {
    setIsMenuClosing(true);
    setTimeout(() => {
      setIsHamburgerOpen(false);
      setIsMenuClosing(false);
    }, 300); // Match this with the animation duration
  };

  return (
    <>
      <Head>
        <title>SubNetx Dashboard</title>
        <meta name="description" content="Monitor network targets in real-time" />
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
          .target-row:hover {
            background-color: ${currentTheme.tableRowHover} !important;
          }
          .details-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 1rem;
          }
          @media (max-width: 768px) {
            .details-grid {
              grid-template-columns: repeat(3, 1fr);
            }
          }
          @media (max-width: 480px) {
            .details-grid {
              grid-template-columns: repeat(2, 1fr);
            }
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
          /* Estilos para el slider */
          input[type="range"] {
            -webkit-appearance: none;
            appearance: none;
            background: transparent;
          }
          input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 16px;
            height: 16px;
            background: #4CAF50;
            border-radius: 50%;
            cursor: pointer;
            margin-top: -5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            transition: all 0.2s ease;
          }
          input[type="range"]::-webkit-slider-thumb:hover {
            transform: scale(1.1);
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
          }
          input[type="range"]::-moz-range-thumb {
            width: 16px;
            height: 16px;
            background: #4CAF50;
            border-radius: 50%;
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            transition: all 0.2s ease;
          }
          input[type="range"]::-moz-range-thumb:hover {
            transform: scale(1.1);
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
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
              onClick={toggleMonitoring}
              className="nav-button"
              disabled={loading}
              style={{
                position: 'relative',
                overflow: 'hidden',
                gap: '2px',
                animation: isMonitoring ? 'pulse 2s infinite' : 'none',
                color: isUpdating ? '#F44336' : isMonitoring ? currentTheme.primary : currentTheme.text
              }}
            >
              <span className="material-icons" style={{
                transform: isMonitoring ? 'scale(1)' : 'scale(1.2)',
                transition: 'all 0.3s ease',
                color: 'inherit',
                fontSize: '20px',
                marginRight: '6px'
              }}>
                {isMonitoring ? 'motion_photos_pause' : 'play_circle'}
              </span>
              <span style={{
                color: 'inherit',
                transition: 'color 0.3s ease',
                fontSize: '0.9rem'
              }}>
                {loading ? 'Loading...' : isMonitoring ? 'Stop' : 'Start'}
              </span>
            </button>

            {/* Logout button */}
            <button
              onClick={handleLogout}
              className="nav-button"
              style={{
                fontSize: '0.9rem'
              }}
            >
              <span className="material-icons" style={{
                transition: 'transform 0.3s ease',
                fontSize: '20px'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateX(3px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateX(0)';
              }}>
                logout
              </span>
              Logout
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
            height: 'calc(100vh - 60px)',
            backgroundColor: `${currentTheme.cardBackground}99`,
            backdropFilter: 'blur(10px)',
            borderLeft: `1px solid ${currentTheme.border}`,
            padding: '2rem 1.5rem',
            zIndex: 999,
            display: isHamburgerOpen ? 'flex' : 'none',
            flexDirection: 'column',
            gap: '1rem',
            boxShadow: '-2px 0 8px rgba(0,0,0,0.1)',
            transform: isHamburgerOpen ? 'translateX(0)' : 'translateX(100%)',
            transition: 'transform 0.3s ease, opacity 0.3s ease',
            opacity: isHamburgerOpen ? 1 : 0
          }}
        >
          <div style={{
            borderBottom: `1px solid ${currentTheme.border}`,
            paddingBottom: '1.5rem',
            marginBottom: '0.5rem'
          }}>
            <h3 style={{
              margin: 0,
              fontSize: '1.3rem',
              color: currentTheme.text,
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <span className="material-icons" style={{ fontSize: '24px', color: currentTheme.primary }}>
                menu
              </span>
              Menu
            </h3>
          </div>

          {!isMonitoring && (
            <button
              onClick={fetchTargets}
              className="nav-button"
              disabled={loading}
              style={{
                width: '100%',
                justifyContent: 'flex-start',
                padding: '1rem 1.25rem',
                borderRadius: '12px',
                transition: 'all 0.2s ease',
                fontSize: '1rem',
                backgroundColor: `${currentTheme.buttonHover}30`,
                border: `1px solid ${currentTheme.border}`
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = `${currentTheme.buttonHover}50`;
                e.currentTarget.style.transform = 'translateX(4px)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = `${currentTheme.buttonHover}30`;
                e.currentTarget.style.transform = 'translateX(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <span className="material-icons" style={{
                animation: isUpdating ? 'spin 1s linear infinite' : 'none',
                marginRight: '12px',
                fontSize: '24px'
              }}>
                refresh
              </span>
              {loading ? 'Loading...' : 'Refresh Data'}
            </button>
          )}

          <div style={{
            backgroundColor: `${currentTheme.buttonHover}20`,
            borderRadius: '12px',
            padding: '1.25rem',
            border: `1px solid ${currentTheme.border}`
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              marginBottom: '1rem'
            }}>
              <span className="material-icons" style={{ fontSize: '24px', color: currentTheme.primary }}>
                settings
              </span>
              <h4 style={{ margin: 0, fontSize: '1.1rem', color: currentTheme.text }}>Settings</h4>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{
                display: 'block',
                marginBottom: '0.75rem',
                fontSize: '0.9rem',
                color: currentTheme.text,
                opacity: 0.9
              }}>
                Monitoring Interval
              </label>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem'
              }}>
                <input
                  type="range"
                  min="5"
                  max="60"
                  value={refreshInterval}
                  onChange={(e) => updateRefreshInterval(parseInt(e.target.value))}
                  style={{
                    flex: 1,
                    height: '6px',
                    borderRadius: '3px',
                    backgroundColor: currentTheme.border,
                    outline: 'none',
                    WebkitAppearance: 'none',
                    appearance: 'none'
                  }}
                />
                <input
                  type="number"
                  min="5"
                  max="60"
                  value={refreshInterval}
                  onChange={(e) => updateRefreshInterval(parseInt(e.target.value))}
                  style={{
                    width: '70px',
                    padding: '0.5rem',
                    borderRadius: '8px',
                    border: `1px solid ${currentTheme.border}`,
                    backgroundColor: currentTheme.background,
                    color: currentTheme.text,
                    fontSize: '0.9rem',
                    textAlign: 'center'
                  }}
                />
              </div>
              <div style={{
                fontSize: '0.8rem',
                color: currentTheme.text,
                opacity: 0.7,
                marginTop: '0.5rem'
              }}>
                {isMonitoring ? `Active - Updates every ${refreshInterval}s` : 'Updates will occur every'}
              </div>
            </div>
          </div>

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
              color: '#F44336'
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
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateX(3px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateX(0)';
            }}>
              logout
            </span>
            Logout
          </button>
        </div>

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
          {/* Welcome Message when no monitoring */}
          {!isMonitoring && !loading && targetsWithStatus.length === 0 && !error && (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: 'calc(100vh - 200px)',
              textAlign: 'center',
              gap: '1rem'
            }}>
              <span className="material-icons" style={{
                fontSize: '64px',
                color: currentTheme.primary,
                animation: 'pulse 2s infinite'
              }}>
                radar
              </span>
              <h2 style={{ margin: 0 }}>Welcome to SubNetx Dashboard</h2>
              <p style={{
                fontSize: '1.1rem',
                color: currentTheme.text,
                maxWidth: '500px',
                lineHeight: '1.5'
              }}>
                Click the <strong>Start</strong> button above to begin monitoring your network targets.
                Real-time statistics and detailed insights will appear here.
              </p>
            </div>
          )}

          {/* Dashboard Panels */}
          {(isMonitoring || targetsWithStatus.length > 0) && (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
              gap: '1rem',
              marginBottom: '2rem'
            }}>
              {/* System Health Card */}
              <div style={{
                backgroundColor: currentTheme.cardBackground,
                padding: '1.2rem',
                borderRadius: '8px',
                border: `1px solid ${currentTheme.border}`,
                transition: 'transform 0.2s, box-shadow 0.2s',
                cursor: 'pointer',
                position: 'relative',
                overflow: 'hidden'
              }}
              onMouseEnter={(e) => {
                const target = e.currentTarget;
                target.style.transform = 'translateY(-2px)';
                target.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
              }}
              onMouseLeave={(e) => {
                const target = e.currentTarget;
                target.style.transform = 'none';
                target.style.boxShadow = 'none';
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  marginBottom: '0.8rem',
                  height: '24px'
                }}>
                  <span className="material-icons" style={{
                    fontSize: '20px',
                    color: currentTheme.primary
                  }}>
                    monitor_heart
                  </span>
                  <h3 style={{ margin: 0, fontSize: '1rem' }}>System Health</h3>
                </div>
                <div style={{ fontSize: '1.8rem', fontWeight: 'bold', marginBottom: '0.4rem' }}>
                  {calculateSystemHealth(targetsWithStatus)}%
                </div>
                <div style={{ fontSize: '0.85rem', color: currentTheme.text }}>
                  {targetsWithStatus.filter(t => t.latestStatus?.status === 'online').length} of {targetsWithStatus.length} hosts online
                </div>
              </div>

              {/* Average RTT Card */}
              <div style={{
                backgroundColor: currentTheme.cardBackground,
                padding: '1.2rem',
                borderRadius: '8px',
                border: `1px solid ${currentTheme.border}`,
                transition: 'transform 0.2s, box-shadow 0.2s',
                cursor: 'pointer',
                position: 'relative',
                overflow: 'hidden'
              }}
              onMouseEnter={(e) => {
                const target = e.currentTarget;
                target.style.transform = 'translateY(-2px)';
                target.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
              }}
              onMouseLeave={(e) => {
                const target = e.currentTarget;
                target.style.transform = 'none';
                target.style.boxShadow = 'none';
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.8rem', height: '24px' }}>
                  <span className="material-icons" style={{ fontSize: '20px', color: currentTheme.primary }}>
                    speed
                  </span>
                  <h3 style={{ margin: 0, fontSize: '1rem' }}>Average RTT</h3>
                </div>
                <div style={{ fontSize: '1.8rem', fontWeight: 'bold', marginBottom: '0.4rem' }}>
                  {calculateAverageRTT(targetsWithStatus)} ms
                </div>
                <div style={{ fontSize: '0.85rem', color: currentTheme.text }}>
                  Round Trip Time
                </div>
              </div>

              {/* Connection Quality Distribution Card */}
              <div style={{
                backgroundColor: currentTheme.cardBackground,
                padding: '1.2rem',
                borderRadius: '8px',
                border: `1px solid ${currentTheme.border}`,
                transition: 'transform 0.2s, box-shadow 0.2s',
                cursor: 'pointer',
                position: 'relative',
                overflow: 'hidden'
              }}
              onMouseEnter={(e) => {
                const target = e.currentTarget;
                target.style.transform = 'translateY(-2px)';
                target.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
              }}
              onMouseLeave={(e) => {
                const target = e.currentTarget;
                target.style.transform = 'none';
                target.style.boxShadow = 'none';
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem', height: '24px' }}>
                  <span className="material-icons" style={{ fontSize: '20px', color: currentTheme.primary }}>
                    signal_cellular_alt
                  </span>
                  <h3 style={{ margin: 0, fontSize: '1rem' }}>Connection Quality</h3>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {/* Excellent Connections */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      backgroundColor: '#4CAF50',
                      display: 'inline-block'
                    }}></span>
                    <span style={{ fontSize: '0.9rem', color: currentTheme.text }}>
                      Excellent: {targetsWithStatus.filter(t => t.latestStatus?.connection_quality === 'excellent').length}
                    </span>
                  </div>
                  {/* Good Connections */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      backgroundColor: '#8BC34A',
                      display: 'inline-block'
                    }}></span>
                    <span style={{ fontSize: '0.9rem', color: currentTheme.text }}>
                      Good: {targetsWithStatus.filter(t => t.latestStatus?.connection_quality === 'good').length}
                    </span>
                  </div>
                  {/* Fair Connections */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      backgroundColor: '#FFC107',
                      display: 'inline-block'
                    }}></span>
                    <span style={{ fontSize: '0.9rem', color: currentTheme.text }}>
                      Fair: {targetsWithStatus.filter(t => t.latestStatus?.connection_quality === 'fair').length}
                    </span>
                  </div>
                  {/* Poor Connections */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      backgroundColor: '#F44336',
                      display: 'inline-block'
                    }}></span>
                    <span style={{ fontSize: '0.9rem', color: currentTheme.text }}>
                      Poor: {targetsWithStatus.filter(t => t.latestStatus?.connection_quality === 'poor').length}
                    </span>
                  </div>
                  {/* No Connection/Unknown */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      backgroundColor: '#9E9E9E',
                      display: 'inline-block'
                    }}></span>
                    <span style={{ fontSize: '0.9rem', color: currentTheme.text }}>
                      No Connection: {targetsWithStatus.filter(t => !t.latestStatus || t.latestStatus.connection_quality === 'none').length}
                    </span>
                  </div>
                </div>
              </div>

              {/* Packet Loss Card */}
              <div style={{
                backgroundColor: currentTheme.cardBackground,
                padding: '1.2rem',
                borderRadius: '8px',
                border: `1px solid ${currentTheme.border}`,
                transition: 'transform 0.2s, box-shadow 0.2s',
                cursor: 'pointer',
                position: 'relative',
                overflow: 'hidden'
              }}
              onMouseEnter={(e) => {
                const target = e.currentTarget;
                target.style.transform = 'translateY(-2px)';
                target.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
              }}
              onMouseLeave={(e) => {
                const target = e.currentTarget;
                target.style.transform = 'none';
                target.style.boxShadow = 'none';
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.8rem', height: '24px' }}>
                  <span className="material-icons" style={{ fontSize: '20px', color: currentTheme.primary }}>
                    error_outline
                  </span>
                  <h3 style={{ margin: 0, fontSize: '1rem' }}>Packet Loss</h3>
                </div>
                <div style={{ fontSize: '1.8rem', fontWeight: 'bold', marginBottom: '0.4rem' }}>
                  {targetsWithStatus.reduce((acc, t) => acc + (t.latestStatus?.packet_loss_percent || 0), 0) / targetsWithStatus.length}%
                </div>
                <div style={{ fontSize: '0.85rem', color: currentTheme.text }}>
                  Average Packet Loss
                </div>
              </div>
            </div>
          )}

          {/* Settings Panel */}
          {showSettings && (
            <div style={{
              position: 'absolute',
              top: '100%',
              right: '1rem',
              backgroundColor: currentTheme.cardBackground,
              borderRadius: '8px',
              border: `1px solid ${currentTheme.border}`,
              padding: '1rem',
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
              zIndex: 1000,
              minWidth: '250px',
              marginTop: '0.5rem'
            }}>
              <div style={{
                borderBottom: `1px solid ${currentTheme.border}`,
                paddingBottom: '0.5rem',
                marginBottom: '1rem'
              }}>
                <h3 style={{ margin: 0, fontSize: '1rem', color: currentTheme.text }}>Settings</h3>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{
                  display: 'block',
                  marginBottom: '0.5rem',
                  fontSize: '0.85rem',
                  color: currentTheme.text
                }}>
                  Monitoring Interval (seconds)
                </label>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <input
                    type="range"
                    min="5"
                    max="60"
                    value={refreshInterval}
                    onChange={(e) => updateRefreshInterval(parseInt(e.target.value))}
                    style={{ flex: 1 }}
                  />
                  <input
                    type="number"
                    min="5"
                    max="60"
                    value={refreshInterval}
                    onChange={(e) => updateRefreshInterval(parseInt(e.target.value))}
                    style={{
                      width: '60px',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      border: `1px solid ${currentTheme.border}`,
                      backgroundColor: currentTheme.background,
                      color: currentTheme.text,
                      fontSize: '0.85rem'
                    }}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Error Message Display */}
          {error && (
            <div style={{
              color: '#F44336',
              marginBottom: '1rem',
              padding: '0.5rem',
              backgroundColor: currentTheme.errorBackground,
              borderRadius: '4px'
            }}>
              Error: {error}
            </div>
          )}

          {/* Targets Table */}
          {targetsWithStatus.length > 0 && (
            <div>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '1rem'
              }}>
                <h2 style={{ margin: 0 }}>Monitored Targets ({targetsWithStatus.length} hosts)</h2>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="material-icons" style={{ color: currentTheme.text, fontSize: '18px' }}>
                    search
                  </span>
                  <input
                    type="text"
                    placeholder="Filter targets..."
                    value={filterText}
                    onChange={(e) => setFilterText(e.target.value)}
                    style={{
                      padding: '4px 12px',
                      borderRadius: '4px',
                      border: `1px solid ${currentTheme.border}`,
                      backgroundColor: currentTheme.background,
                      color: currentTheme.text,
                      width: '200px',
                      fontSize: '0.9rem'
                    }}
                  />
                </div>
              </div>

              <div style={{ overflowX: 'auto' }}>
                <table style={{
                  width: '100%',
                  borderCollapse: 'separate',
                  borderSpacing: '0',
                  backgroundColor: currentTheme.cardBackground,
                  borderRadius: '8px',
                  overflow: 'hidden',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                }}>
                  <thead>
                    <tr style={{
                      backgroundColor: currentTheme.tableHeader,
                      height: '40px'
                    }}>
                      <th style={{
                        padding: '8px 12px',
                        textAlign: 'left',
                        cursor: 'pointer',
                        userSelect: 'none',
                        position: 'relative',
                        backgroundColor: sortConfig?.key === 'id' ? `${currentTheme.primary}15` : 'transparent',
                        transition: 'all 0.2s ease',
                        borderBottom: `2px solid ${currentTheme.border}`,
                        fontSize: '0.85rem',
                        fontWeight: '600',
                        color: currentTheme.text,
                        opacity: 0.9
                      }}
                      onClick={() => requestSort('id')}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = `${currentTheme.primary}25`;
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = sortConfig?.key === 'id' ? `${currentTheme.primary}15` : 'transparent';
                      }}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          whiteSpace: 'nowrap'
                        }}>
                          ID
                          <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '2px'
                          }}>
                            <span className="material-icons" style={{
                              fontSize: '14px',
                              opacity: sortConfig?.key === 'id' ? 1 : 0.5,
                              color: currentTheme.primary
                            }}>
                              {sortConfig?.key === 'id'
                                ? (sortConfig.direction === 'ascending' ? 'arrow_upward' : 'arrow_downward')
                                : 'sort'
                              }
                            </span>
                            <span style={{
                              fontSize: '10px',
                              opacity: 0.6,
                              color: currentTheme.primary
                            }}>123</span>
                          </div>
                        </div>
                      </th>
                      <th style={{
                        padding: '8px 12px',
                        textAlign: 'left',
                        cursor: 'pointer',
                        userSelect: 'none',
                        position: 'relative',
                        backgroundColor: sortConfig?.key === 'target' ? `${currentTheme.primary}15` : 'transparent',
                        transition: 'all 0.2s ease',
                        borderBottom: `2px solid ${currentTheme.border}`,
                        fontSize: '0.85rem',
                        fontWeight: '600',
                        color: currentTheme.text,
                        opacity: 0.9
                      }}
                      onClick={() => requestSort('target')}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = `${currentTheme.primary}25`;
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = sortConfig?.key === 'target' ? `${currentTheme.primary}15` : 'transparent';
                      }}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          whiteSpace: 'nowrap'
                        }}>
                          Target
                          <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '2px'
                          }}>
                            <span className="material-icons" style={{
                              fontSize: '14px',
                              opacity: sortConfig?.key === 'target' ? 1 : 0.5,
                              color: currentTheme.primary
                            }}>
                              {sortConfig?.key === 'target'
                                ? (sortConfig.direction === 'ascending' ? 'arrow_upward' : 'arrow_downward')
                                : 'sort_by_alpha'
                              }
                            </span>
                            <span style={{
                              fontSize: '10px',
                              opacity: 0.6,
                              color: currentTheme.primary
                            }}>aZ</span>
                          </div>
                        </div>
                      </th>
                      <th style={{
                        padding: '8px 12px',
                        textAlign: 'left',
                        cursor: 'pointer',
                        userSelect: 'none',
                        position: 'relative',
                        backgroundColor: sortConfig?.key === 'timestamp' ? `${currentTheme.primary}15` : 'transparent',
                        transition: 'all 0.2s ease',
                        borderBottom: `2px solid ${currentTheme.border}`,
                        fontSize: '0.85rem',
                        fontWeight: '600',
                        color: currentTheme.text,
                        opacity: 0.9
                      }}
                      onClick={() => requestSort('timestamp')}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = `${currentTheme.primary}25`;
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = sortConfig?.key === 'timestamp' ? `${currentTheme.primary}15` : 'transparent';
                      }}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          whiteSpace: 'nowrap'
                        }}>
                          Last Update
                          <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '2px'
                          }}>
                            <span className="material-icons" style={{
                              fontSize: '14px',
                              opacity: sortConfig?.key === 'timestamp' ? 1 : 0.5,
                              color: currentTheme.primary
                            }}>
                              {sortConfig?.key === 'timestamp'
                                ? (sortConfig.direction === 'ascending' ? 'arrow_upward' : 'arrow_downward')
                                : 'sort'
                              }
                            </span>
                            <span style={{
                              fontSize: '10px',
                              opacity: 0.6,
                              color: currentTheme.primary
                            }}>123</span>
                          </div>
                        </div>
                      </th>
                      <th style={{
                        padding: '8px 12px',
                        textAlign: 'left',
                        cursor: 'pointer',
                        userSelect: 'none',
                        position: 'relative',
                        backgroundColor: sortConfig?.key === 'status' ? `${currentTheme.primary}15` : 'transparent',
                        transition: 'all 0.2s ease',
                        borderBottom: `2px solid ${currentTheme.border}`,
                        fontSize: '0.85rem',
                        fontWeight: '600',
                        color: currentTheme.text,
                        opacity: 0.9
                      }}
                      onClick={() => requestSort('status')}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = `${currentTheme.primary}25`;
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = sortConfig?.key === 'status' ? `${currentTheme.primary}15` : 'transparent';
                      }}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          whiteSpace: 'nowrap'
                        }}>
                          Status
                          <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '2px'
                          }}>
                            <span className="material-icons" style={{
                              fontSize: '14px',
                              opacity: sortConfig?.key === 'status' ? 1 : 0.5,
                              color: currentTheme.primary
                            }}>
                              {sortConfig?.key === 'status'
                                ? (sortConfig.direction === 'ascending' ? 'arrow_upward' : 'arrow_downward')
                                : 'sort'
                              }
                            </span>
                            <span style={{
                              fontSize: '10px',
                              opacity: 0.6,
                              color: currentTheme.primary
                            }}>123</span>
                          </div>
                        </div>
                      </th>
                      <th style={{
                        padding: '8px 12px',
                        textAlign: 'left',
                        cursor: 'pointer',
                        userSelect: 'none',
                        position: 'relative',
                        backgroundColor: sortConfig?.key === 'quality' ? `${currentTheme.primary}15` : 'transparent',
                        transition: 'all 0.2s ease',
                        borderBottom: `2px solid ${currentTheme.border}`,
                        fontSize: '0.85rem',
                        fontWeight: '600',
                        color: currentTheme.text,
                        opacity: 0.9
                      }}
                      onClick={() => requestSort('quality')}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = `${currentTheme.primary}25`;
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = sortConfig?.key === 'quality' ? `${currentTheme.primary}15` : 'transparent';
                      }}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          whiteSpace: 'nowrap'
                        }}>
                          Quality
                          <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '2px'
                          }}>
                            <span className="material-icons" style={{
                              fontSize: '14px',
                              opacity: sortConfig?.key === 'quality' ? 1 : 0.5,
                              color: currentTheme.primary
                            }}>
                              {sortConfig?.key === 'quality'
                                ? (sortConfig.direction === 'ascending' ? 'arrow_upward' : 'arrow_downward')
                                : 'sort'
                              }
                            </span>
                            <span style={{
                              fontSize: '10px',
                              opacity: 0.6,
                              color: currentTheme.primary
                            }}>123</span>
                          </div>
                        </div>
                      </th>
                      <th style={{
                        padding: '8px 12px',
                        textAlign: 'left',
                        cursor: 'pointer',
                        userSelect: 'none',
                        position: 'relative',
                        backgroundColor: sortConfig?.key === 'packetLoss' ? `${currentTheme.primary}15` : 'transparent',
                        transition: 'all 0.2s ease',
                        borderBottom: `2px solid ${currentTheme.border}`,
                        fontSize: '0.85rem',
                        fontWeight: '600',
                        color: currentTheme.text,
                        opacity: 0.9
                      }}
                      onClick={() => requestSort('packetLoss')}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = `${currentTheme.primary}25`;
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = sortConfig?.key === 'packetLoss' ? `${currentTheme.primary}15` : 'transparent';
                      }}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          whiteSpace: 'nowrap'
                        }}>
                          Packet Loss
                          <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '2px'
                          }}>
                            <span className="material-icons" style={{
                              fontSize: '14px',
                              opacity: sortConfig?.key === 'packetLoss' ? 1 : 0.5,
                              color: currentTheme.primary
                            }}>
                              {sortConfig?.key === 'packetLoss'
                                ? (sortConfig.direction === 'ascending' ? 'arrow_upward' : 'arrow_downward')
                                : 'sort'
                              }
                            </span>
                            <span style={{
                              fontSize: '10px',
                              opacity: 0.6,
                              color: currentTheme.primary
                            }}>123</span>
                          </div>
                        </div>
                      </th>
                      <th style={{
                        padding: '8px 12px',
                        textAlign: 'left',
                        cursor: 'pointer',
                        userSelect: 'none',
                        position: 'relative',
                        backgroundColor: sortConfig?.key === 'avgRtt' ? `${currentTheme.primary}15` : 'transparent',
                        transition: 'all 0.2s ease',
                        borderBottom: `2px solid ${currentTheme.border}`,
                        fontSize: '0.85rem',
                        fontWeight: '600',
                        color: currentTheme.text,
                        opacity: 0.9
                      }}
                      onClick={() => requestSort('avgRtt')}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = `${currentTheme.primary}25`;
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = sortConfig?.key === 'avgRtt' ? `${currentTheme.primary}15` : 'transparent';
                      }}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          whiteSpace: 'nowrap'
                        }}>
                          Avg RTT
                          <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '2px'
                          }}>
                            <span className="material-icons" style={{
                              fontSize: '14px',
                              opacity: sortConfig?.key === 'avgRtt' ? 1 : 0.5,
                              color: currentTheme.primary
                            }}>
                              {sortConfig?.key === 'avgRtt'
                                ? (sortConfig.direction === 'ascending' ? 'arrow_upward' : 'arrow_downward')
                                : 'sort'
                              }
                            </span>
                            <span style={{
                              fontSize: '10px',
                              opacity: 0.6,
                              color: currentTheme.primary
                            }}>123</span>
                          </div>
                        </div>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortData(filterData(targetsWithStatus)).map(({ target, latestStatus }, index) => (
                      <tr
                        key={target.id}
                        style={{
                          backgroundColor: latestStatus?.status === 'timeout'
                            ? `${currentTheme.errorBackground}80`
                            : index % 2 === 0
                              ? currentTheme.tableRow
                              : `${currentTheme.tableRowHover}30`,
                          transition: 'all 0.2s ease'
                        }}
                        className="target-row"
                      >
                        <td style={{
                          padding: '8px 12px',
                          fontSize: '0.85rem',
                          borderBottom: `1px solid ${currentTheme.border}30`
                        }}>{target.id}</td>
                        <td style={{
                          padding: '8px 12px',
                          fontSize: '0.85rem',
                          fontWeight: '500',
                          borderBottom: `1px solid ${currentTheme.border}30`
                        }}>{target.target}</td>
                        <td style={{
                          padding: '8px 12px',
                          fontSize: '0.85rem',
                          color: `${currentTheme.text}90`,
                          borderBottom: `1px solid ${currentTheme.border}30`
                        }}>
                          {latestStatus ? new Date(latestStatus.timestamp).toLocaleString() : 'N/A'}
                        </td>
                        <td style={{
                          padding: '8px 12px',
                          fontSize: '0.85rem',
                          borderBottom: `1px solid ${currentTheme.border}30`
                        }}>
                          <div style={{
                            color: latestStatus?.status === 'online' ? '#4CAF50' : '#F44336',
                            fontWeight: '500',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}>
                            <span style={{
                              width: '8px',
                              height: '8px',
                              borderRadius: '50%',
                              backgroundColor: latestStatus?.status === 'online' ? '#4CAF50' : '#F44336',
                              display: 'inline-block'
                            }}></span>
                            {latestStatus?.status || 'N/A'}
                          </div>
                        </td>
                        <td style={{
                          padding: '8px 12px',
                          fontSize: '0.85rem',
                          borderBottom: `1px solid ${currentTheme.border}30`
                        }}>
                          <div style={{
                            color: getStatusColor(latestStatus?.connection_quality || 'none'),
                            fontWeight: '500',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}>
                            <span style={{
                              width: '8px',
                              height: '8px',
                              borderRadius: '50%',
                              backgroundColor: getStatusColor(latestStatus?.connection_quality || 'none'),
                              display: 'inline-block'
                            }}></span>
                            {latestStatus?.connection_quality || 'N/A'}
                          </div>
                        </td>
                        <td style={{
                          padding: '8px 12px',
                          fontSize: '0.85rem',
                          borderBottom: `1px solid ${currentTheme.border}30`
                        }}>
                          {latestStatus ? (
                            <div style={{
                              color: latestStatus.packet_loss_percent > 0 ? '#F44336' : '#4CAF50',
                              fontWeight: '500',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px'
                            }}>
                              <span style={{
                                width: '8px',
                                height: '8px',
                                borderRadius: '50%',
                                backgroundColor: latestStatus.packet_loss_percent > 0 ? '#F44336' : '#4CAF50',
                                display: 'inline-block'
                              }}></span>
                              {latestStatus.packet_loss_percent}%
                            </div>
                          ) : 'N/A'}
                        </td>
                        <td style={{
                          padding: '8px 12px',
                          fontSize: '0.85rem',
                          fontWeight: '500',
                          borderBottom: `1px solid ${currentTheme.border}30`
                        }}>
                          {latestStatus ? (
                            <div style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px'
                            }}>
                              <span style={{
                                width: '8px',
                                height: '8px',
                                borderRadius: '50%',
                                backgroundColor: latestStatus.avg_rtt > 100 ? '#F44336' :
                                               latestStatus.avg_rtt > 50 ? '#FF9800' : '#4CAF50',
                                display: 'inline-block'
                              }}></span>
                              {latestStatus.avg_rtt}
                            </div>
                          ) : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Detailed Online Targets Information */}
              {targetsWithStatus.map(({ target, latestStatus }) => (
                latestStatus && latestStatus.status === 'online' && (
                  <div key={`detail-${target.id}`} style={{
                    marginTop: '1rem',
                    padding: '0.75rem',
                    border: `1px solid ${currentTheme.border}`,
                    borderRadius: '8px',
                    backgroundColor: currentTheme.cardBackground
                  }}>
                    {/* Header with target info */}
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      marginBottom: '0.5rem'
                    }}>
                      <div style={{ flex: 1 }}>
                        <div style={{
                          fontSize: '1rem',
                          fontWeight: '500',
                          color: currentTheme.text
                        }}>
                          {target.target}
                        </div>
                        <div style={{
                          fontSize: '0.75rem',
                          color: currentTheme.text,
                          opacity: 0.7
                        }}>
                          Last Update: {new Date(latestStatus.timestamp).toLocaleString()}
                        </div>
                      </div>
                    </div>

                    {/* Stats Grid */}
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                      gap: '0.5rem',
                      marginBottom: '0.5rem'
                    }}>
                      {/* RTT Stats */}
                      <div style={{
                        padding: '0.5rem',
                        backgroundColor: currentTheme.background,
                        borderRadius: '6px',
                        border: `1px solid ${currentTheme.border}`
                      }}>
                        <div style={{ fontSize: '0.85rem', color: currentTheme.text, marginBottom: '0.25rem' }}>
                          RTT Statistics
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.25rem' }}>
                          <div>
                            <div style={{ color: currentTheme.text, opacity: 0.8, fontSize: '0.75rem' }}>Min</div>
                            <div style={{ color: '#4CAF50', fontWeight: '500' }}>{latestStatus.min_rtt} ms</div>
                          </div>
                          <div>
                            <div style={{ color: currentTheme.text, opacity: 0.8, fontSize: '0.75rem' }}>Max</div>
                            <div style={{ color: '#F44336', fontWeight: '500' }}>{latestStatus.max_rtt} ms</div>
                          </div>
                          <div>
                            <div style={{ color: currentTheme.text, opacity: 0.8, fontSize: '0.75rem' }}>Avg</div>
                            <div style={{ color: '#2196F3', fontWeight: '500' }}>{latestStatus.avg_rtt} ms</div>
                          </div>
                          <div>
                            <div style={{ color: currentTheme.text, opacity: 0.8, fontSize: '0.75rem' }}>Mdev</div>
                            <div style={{ color: '#FF9800', fontWeight: '500' }}>{latestStatus.mdev_rtt} ms</div>
                          </div>
                        </div>
                      </div>

                      {/* Packet Stats */}
                      <div style={{
                        padding: '0.5rem',
                        backgroundColor: currentTheme.background,
                        borderRadius: '6px',
                        border: `1px solid ${currentTheme.border}`
                      }}>
                        <div style={{ fontSize: '0.85rem', color: currentTheme.text, marginBottom: '0.25rem' }}>
                          Packet Statistics
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.25rem' }}>
                          <div>
                            <div style={{ color: currentTheme.text, opacity: 0.8, fontSize: '0.75rem' }}>Transmitted</div>
                            <div style={{ color: currentTheme.primary, fontWeight: '500' }}>
                              {latestStatus.packets_transmitted}
                            </div>
                          </div>
                          <div>
                            <div style={{ color: currentTheme.text, opacity: 0.8, fontSize: '0.75rem' }}>Received</div>
                            <div style={{ color: currentTheme.primary, fontWeight: '500' }}>
                              {latestStatus.packets_received}
                            </div>
                          </div>
                          <div style={{ gridColumn: '1 / -1' }}>
                            <div style={{ color: currentTheme.text, opacity: 0.8, fontSize: '0.75rem' }}>Packet Loss</div>
                            <div style={{
                              color: latestStatus.packet_loss_percent > 0 ? '#F44336' : '#4CAF50',
                              fontWeight: '500'
                            }}>
                              {latestStatus.packet_loss_percent}%
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* ICMP Response Details */}
                      <div style={{
                        padding: '0.5rem',
                        backgroundColor: currentTheme.background,
                        borderRadius: '6px',
                        border: `1px solid ${currentTheme.border}`
                      }}>
                        <div style={{ fontSize: '0.85rem', color: currentTheme.text, marginBottom: '0.25rem' }}>
                          ICMP Response Times
                        </div>
                        <div style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(5, 1fr)',
                          gap: '0.25rem'
                        }}>
                          {latestStatus.icmp_details.map((ping, index) => (
                            <div key={index} style={{
                              textAlign: 'center',
                              padding: '0.25rem',
                              borderRadius: '4px',
                              backgroundColor: currentTheme.cardBackground
                            }}>
                              <div style={{
                                fontSize: '0.9rem',
                                fontWeight: '500',
                                color: ping.response_time_ms > 100 ? '#F44336' :
                                      ping.response_time_ms > 50 ? '#FF9800' : '#4CAF50'
                              }}>
                                {ping.response_time_ms.toFixed(1)}
                              </div>
                              <div style={{
                                fontSize: '0.65rem',
                                color: currentTheme.text,
                                opacity: 0.6
                              }}>
                                seq {ping.sequence}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* TLS Info if available */}
                      {latestStatus.tls_info.cert_expiry && (
                        <div style={{
                          padding: '0.5rem',
                          backgroundColor: currentTheme.background,
                          borderRadius: '6px',
                          border: `1px solid ${currentTheme.border}`
                        }}>
                          <div style={{ fontSize: '0.85rem', color: currentTheme.text, marginBottom: '0.25rem' }}>
                            TLS Information
                          </div>
                          <div style={{ fontSize: '0.75rem', color: currentTheme.text }}>
                            <div style={{ marginBottom: '0.25rem' }}>
                              <span style={{ opacity: 0.8 }}>Expires:</span>{' '}
                              {new Date(latestStatus.tls_info.cert_expiry).toLocaleDateString()}
                            </div>
                            {latestStatus.tls_info.issuer && (
                              <div style={{ marginBottom: '0.25rem' }}>
                                <span style={{ opacity: 0.8 }}>Issuer:</span>{' '}
                                {latestStatus.tls_info.issuer}
                              </div>
                            )}
                            {latestStatus.tls_info.version && (
                              <div>
                                <span style={{ opacity: 0.8 }}>Version:</span>{' '}
                                {latestStatus.tls_info.version}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )
              ))}
            </div>
          )}
        </main>

        <footer style={{
          backgroundColor: `${currentTheme.cardBackground}99`, // Added some transparency
          backdropFilter: 'blur(10px)',
          padding: '0.6rem',
          borderTop: `1px solid ${currentTheme.border}`,
          width: '100%',
          boxSizing: 'border-box',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '0.5rem',
          flexShrink: 0,
          position: 'relative',
          zIndex: 1
        }}>
          <div style={{
            fontSize: '0.85rem',
            color: currentTheme.text,
            opacity: 0.8
          }}>
            © {new Date().getFullYear()} SubNetx. Released under the MIT License.
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1.5rem'
          }}>
            <a
              href="mailto:tacoronteriverocristian@gmail.com"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                color: currentTheme.text,
                textDecoration: 'none',
                transition: 'color 0.2s',
                fontSize: '0.85rem'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = currentTheme.primary;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = currentTheme.text;
              }}
            >
              <span className="material-icons" style={{ fontSize: '16px' }}>email</span>
              Contact
            </a>
            <a
              href="https://github.com/TacoronteRiveroCristian/SubNetx"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                color: currentTheme.text,
                textDecoration: 'none',
                transition: 'color 0.2s',
                fontSize: '0.85rem'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = currentTheme.primary;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = currentTheme.text;
              }}
            >
              <span className="material-icons" style={{ fontSize: '16px' }}>code</span>
              GitHub
            </a>
          </div>
        </footer>
      </div>
    </>
  );
}
