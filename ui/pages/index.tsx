// pages/index.tsx
import Head from 'next/head';
import { useRouter } from 'next/router'; // Import useRouter for navigation to login page
import { useEffect, useRef, useState } from 'react';

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

export default function Home() {
  // Add router for navigation to login page
  const router = useRouter();

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
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  // State to track if settings panel is open
  const [showSettings, setShowSettings] = useState(false);
  // State to track refresh interval
  const [refreshInterval, setRefreshInterval] = useState(10);
  // State to track when data is being updated
  const [isUpdating, setIsUpdating] = useState(false);
  // Ref to store the interval ID for cleanup
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  // Add these new states at the top with other states
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: 'ascending' | 'descending';
  } | null>(null);
  const [filterText, setFilterText] = useState('');

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

  // Add this sorting function before the return statement
  const sortData = (data: TargetWithStatus[]) => {
    if (!sortConfig) return data;

    return [...data].sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortConfig.key) {
        case 'id':
          aValue = a.target.id;
          bValue = b.target.id;
          break;
        case 'target':
          aValue = a.target.target;
          bValue = b.target.target;
          break;
        case 'status':
          aValue = a.latestStatus?.status || '';
          bValue = b.latestStatus?.status || '';
          break;
        case 'quality':
          aValue = a.latestStatus?.connection_quality || '';
          bValue = b.latestStatus?.connection_quality || '';
          break;
        case 'packetLoss':
          aValue = a.latestStatus?.packet_loss_percent || 0;
          bValue = b.latestStatus?.packet_loss_percent || 0;
          break;
        case 'avgRtt':
          aValue = a.latestStatus?.avg_rtt || 0;
          bValue = b.latestStatus?.avg_rtt || 0;
          break;
        default:
          return 0;
      }

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

  return (
    <>
      <Head>
        <title>SubNetx</title>
        <meta name="description" content="Monitor network targets in real-time" />
        <link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons" />
        <style>{`
          body {
            margin: 0;
            padding: 0;
            background-color: ${currentTheme.background};
            color: ${currentTheme.text};
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            overflow: hidden;
            height: 100vh;
            width: 100vw;
          }
          #__next {
            height: 100%;
            display: flex;
            flex-direction: column;
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
        `}</style>
      </Head>

      <div style={{
        backgroundColor: currentTheme.navbar,
        padding: '0.5rem 1.5rem',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        position: 'sticky',
        top: 0,
        zIndex: 1000,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span className="material-icons" style={{ color: currentTheme.text, fontSize: '22px' }}>
            wifi_tethering
          </span>
          <h1 style={{ margin: 0, fontSize: '1.1rem' }}>SubNetx</h1>
        </div>

        <div style={{ display: 'flex', gap: '4px' }}>
          <button
            onClick={toggleMonitoring}
            className="nav-button"
            disabled={loading}
          >
            <span className="material-icons">
              {isMonitoring ? 'stop' : 'play_arrow'}
            </span>
            {loading ? 'Loading...' : isMonitoring ? 'Stop' : 'Start'}
          </button>

          {!isMonitoring && (
            <button
              onClick={fetchTargets}
              className="nav-button"
              disabled={loading}
            >
              <span className="material-icons">refresh</span>
              {loading ? 'Loading...' : 'Refresh'}
            </button>
          )}

          <button
            onClick={() => setShowSettings(!showSettings)}
            className="nav-button"
          >
            <span className="material-icons">settings</span>
            Settings
          </button>

          <button
            onClick={toggleTheme}
            className="nav-button"
          >
            <span className="material-icons">
              {theme === 'light' ? 'dark_mode' : 'light_mode'}
            </span>
            {theme === 'light' ? 'Dark' : 'Light'}
          </button>

          {/* Add logout button */}
          <button
            onClick={handleLogout}
            className="nav-button"
          >
            <span className="material-icons">logout</span>
            Logout
          </button>
        </div>
      </div>

      <main style={{
        padding: '2rem',
        backgroundColor: currentTheme.background,
        color: currentTheme.text,
        flex: 1,
        overflowY: 'auto',
        width: '100%',
        boxSizing: 'border-box'
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
            <h2 style={{ margin: 0 }}>Welcome to SubNetx</h2>
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

        {/* Only show dashboard cards when monitoring is active and we have data */}
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
                  color: calculateSystemHealth(targetsWithStatus) >= 80 ? '#4CAF50' :
                         calculateSystemHealth(targetsWithStatus) >= 60 ? '#FF9800' : '#F44336'
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
                <span className="material-icons" style={{
                  fontSize: '20px',
                  color: calculateAverageRTT(targetsWithStatus) <= 50 ? '#4CAF50' :
                         calculateAverageRTT(targetsWithStatus) <= 100 ? '#FF9800' : '#F44336'
                }}>
                  speed
                </span>
                <h3 style={{ margin: 0, fontSize: '1rem' }}>Average RTT</h3>
              </div>
              <div style={{ fontSize: '1.8rem', fontWeight: 'bold', marginBottom: '0.4rem' }}>
                {calculateAverageRTT(targetsWithStatus)} ms
              </div>
              <div style={{ fontSize: '0.85rem', color: currentTheme.text }}>
                Network Latency
              </div>
            </div>

            {/* Connection Quality Card */}
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
                  signal_cellular_alt
                </span>
                <h3 style={{ margin: 0, fontSize: '1rem' }}>Connection Quality</h3>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {Object.entries(getConnectionQualityDistribution(targetsWithStatus))
                  .filter(([quality]) => quality !== 'excellent' && quality !== 'none')
                  .map(([quality, count]) => (
                    <div key={quality} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <div style={{
                          width: '6px',
                          height: '6px',
                          borderRadius: '50%',
                          backgroundColor: quality === 'Excellent' ? '#4CAF50' :
                                         quality === 'Good' ? '#8BC34A' :
                                         quality === 'Fair' ? '#FF9800' :
                                         quality === 'Poor' ? '#F44336' : '#9E9E9E'
                        }}></div>
                        <span style={{ fontSize: '0.85rem' }}>{quality}</span>
                      </div>
                      <span style={{ fontWeight: 'bold', fontSize: '0.85rem' }}>{count}</span>
                    </div>
                  ))}
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
            backgroundColor: currentTheme.cardBackground,
            padding: '1rem',
            borderRadius: '4px',
            marginBottom: '1rem',
            border: `1px solid ${currentTheme.border}`
          }}>
            <h2 style={{ marginTop: 0 }}>Settings</h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <label htmlFor="refreshInterval">Refresh Interval (seconds):</label>
              <input
                type="number"
                id="refreshInterval"
                min="5"
                max="60"
                value={refreshInterval}
                onChange={(e) => updateRefreshInterval(Number(e.target.value))}
                style={{
                  padding: '0.5rem',
                  borderRadius: '4px',
                  border: `1px solid ${currentTheme.border}`,
                  backgroundColor: currentTheme.background,
                  color: currentTheme.text,
                  width: '80px'
                }}
              />
              <span style={{ color: currentTheme.text }}>
                {isMonitoring ? `(Active - Updates every ${refreshInterval}s)` : ''}
              </span>
            </div>
          </div>
        )}

        {/* Display monitoring status */}
        {isMonitoring && (
          <div style={{
            backgroundColor: currentTheme.statusIndicator,
            padding: '0.5rem 1rem',
            borderRadius: '4px',
            marginBottom: '1rem',
            display: 'flex',
            alignItems: 'center',
            color: currentTheme.text
          }}>
            <div style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: isUpdating ? '#F44336' : currentTheme.secondary,
              marginRight: '8px',
              animation: isUpdating ? 'none' : 'pulse 2s infinite'
            }}></div>
            <style jsx>{`
              @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.3; }
                100% { opacity: 1; }
              }
            `}</style>
            Monitoring active - Data refreshes every {refreshInterval} seconds
          </div>
        )}

        {/* Display error message if any */}
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

        {/* Display the fetched targets with their latest status */}
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
            <table style={{
              borderCollapse: 'collapse',
              width: '100%',
              marginBottom: '2rem',
              backgroundColor: currentTheme.background
            }}>
              <thead>
                <tr style={{ backgroundColor: currentTheme.tableHeader }}>
                  <th
                    onClick={() => requestSort('id')}
                    style={{
                      border: `1px solid ${currentTheme.border}`,
                      padding: '8px',
                      textAlign: 'left',
                      cursor: 'pointer',
                      userSelect: 'none'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      ID
                      <span className="material-icons" style={{ fontSize: '16px' }}>
                        {sortConfig?.key === 'id'
                          ? sortConfig.direction === 'ascending'
                            ? 'arrow_upward'
                            : 'arrow_downward'
                          : 'unfold_more'
                        }
                      </span>
                    </div>
                  </th>
                  <th
                    onClick={() => requestSort('target')}
                    style={{
                      border: `1px solid ${currentTheme.border}`,
                      padding: '8px',
                      textAlign: 'left',
                      cursor: 'pointer',
                      userSelect: 'none'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      Target
                      <span className="material-icons" style={{ fontSize: '16px' }}>
                        {sortConfig?.key === 'target'
                          ? sortConfig.direction === 'ascending'
                            ? 'arrow_upward'
                            : 'arrow_downward'
                          : 'unfold_more'
                        }
                      </span>
                    </div>
                  </th>
                  <th
                    onClick={() => requestSort('status')}
                    style={{
                      border: `1px solid ${currentTheme.border}`,
                      padding: '8px',
                      textAlign: 'left',
                      cursor: 'pointer',
                      userSelect: 'none'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      Status
                      <span className="material-icons" style={{ fontSize: '16px' }}>
                        {sortConfig?.key === 'status'
                          ? sortConfig.direction === 'ascending'
                            ? 'arrow_upward'
                            : 'arrow_downward'
                          : 'unfold_more'
                        }
                      </span>
                    </div>
                  </th>
                  <th style={{ border: `1px solid ${currentTheme.border}`, padding: '8px', textAlign: 'left' }}>Last Updated</th>
                  <th
                    onClick={() => requestSort('quality')}
                    style={{
                      border: `1px solid ${currentTheme.border}`,
                      padding: '8px',
                      textAlign: 'left',
                      cursor: 'pointer',
                      userSelect: 'none'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      Connection Quality
                      <span className="material-icons" style={{ fontSize: '16px' }}>
                        {sortConfig?.key === 'quality'
                          ? sortConfig.direction === 'ascending'
                            ? 'arrow_upward'
                            : 'arrow_downward'
                          : 'unfold_more'
                        }
                      </span>
                    </div>
                  </th>
                  <th
                    onClick={() => requestSort('packetLoss')}
                    style={{
                      border: `1px solid ${currentTheme.border}`,
                      padding: '8px',
                      textAlign: 'left',
                      cursor: 'pointer',
                      userSelect: 'none'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      Packet Loss
                      <span className="material-icons" style={{ fontSize: '16px' }}>
                        {sortConfig?.key === 'packetLoss'
                          ? sortConfig.direction === 'ascending'
                            ? 'arrow_upward'
                            : 'arrow_downward'
                          : 'unfold_more'
                        }
                      </span>
                    </div>
                  </th>
                  <th
                    onClick={() => requestSort('avgRtt')}
                    style={{
                      border: `1px solid ${currentTheme.border}`,
                      padding: '8px',
                      textAlign: 'left',
                      cursor: 'pointer',
                      userSelect: 'none'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      Avg RTT (ms)
                      <span className="material-icons" style={{ fontSize: '16px' }}>
                        {sortConfig?.key === 'avgRtt'
                          ? sortConfig.direction === 'ascending'
                            ? 'arrow_upward'
                            : 'arrow_downward'
                          : 'unfold_more'
                        }
                      </span>
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody>
                {sortData(filterData(targetsWithStatus)).map(({ target, latestStatus }) => (
                  <tr
                    key={target.id}
                    style={{
                      backgroundColor: latestStatus?.status === 'timeout' ? currentTheme.errorBackground : currentTheme.tableRow
                    }}
                    className="target-row"
                    onMouseEnter={(e) => {
                      // Apply hover style manually
                      (e.currentTarget as HTMLElement).style.backgroundColor = currentTheme.tableRowHover;
                    }}
                    onMouseLeave={(e) => {
                      // Restore original style
                      (e.currentTarget as HTMLElement).style.backgroundColor =
                        latestStatus?.status === 'timeout' ? currentTheme.errorBackground : currentTheme.tableRow;
                    }}
                  >
                    <td style={{ border: `1px solid ${currentTheme.border}`, padding: '8px' }}>{target.id}</td>
                    <td style={{ border: `1px solid ${currentTheme.border}`, padding: '8px', fontWeight: 'bold' }}>{target.target}</td>
                    <td style={{ border: `1px solid ${currentTheme.border}`, padding: '8px' }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        fontWeight: 'bold',
                        color: latestStatus?.status === 'online' ? '#4CAF50' : '#F44336'
                      }}>
                        <div style={{
                          width: '10px',
                          height: '10px',
                          borderRadius: '50%',
                          backgroundColor: latestStatus?.status === 'online' ? '#4CAF50' : '#F44336',
                          marginRight: '8px'
                        }}></div>
                        {latestStatus?.status || 'Unknown'}
                      </div>
                    </td>
                    <td style={{ border: `1px solid ${currentTheme.border}`, padding: '8px' }}>
                      {latestStatus ? formatDate(latestStatus.timestamp) : 'N/A'}
                    </td>
                    <td style={{ border: `1px solid ${currentTheme.border}`, padding: '8px' }}>
                      {latestStatus ? (
                        <div style={{
                          backgroundColor: getStatusColor(latestStatus.connection_quality),
                          color: 'white',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          display: 'inline-block',
                          textTransform: 'capitalize',
                          fontWeight: 'bold',
                          fontSize: '0.8rem'
                        }}>
                          {latestStatus.connection_quality}
                        </div>
                      ) : 'N/A'}
                    </td>
                    <td style={{ border: `1px solid ${currentTheme.border}`, padding: '8px' }}>
                      {latestStatus ? (
                        <div style={{
                          color: latestStatus.packet_loss_percent > 0 ? '#F44336' : '#4CAF50',
                          fontWeight: 'bold'
                        }}>
                          {latestStatus.packet_loss_percent}%
                        </div>
                      ) : 'N/A'}
                    </td>
                    <td style={{ border: `1px solid ${currentTheme.border}`, padding: '8px', fontWeight: 'bold' }}>
                      {latestStatus?.avg_rtt || 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Detailed ICMP response visualization for each target */}
            {targetsWithStatus.map(({ target, latestStatus }) => (
              latestStatus && latestStatus.icmp_details.length > 0 && (
                <div key={`detail-${target.id}`} style={{
                  marginBottom: '1rem',
                  padding: '0.5rem',
                  border: `1px solid ${currentTheme.border}`,
                  borderRadius: '4px',
                  backgroundColor: currentTheme.cardBackground
                }}>
                  <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.2rem' }}>ICMP Response Details: {target.target}</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '0.5rem' }}>
                    {latestStatus.icmp_details.map((ping, index) => (
                      <div key={index} style={{
                        padding: '0.3rem',
                        backgroundColor: currentTheme.background,
                        border: `1px solid ${currentTheme.border}`,
                        borderRadius: '4px',
                        textAlign: 'center'
                      }}>
                        <div style={{ fontSize: '0.8rem', color: currentTheme.text }}>Sequence {ping.sequence}</div>
                        <div style={{
                          fontSize: '1.2rem',
                          fontWeight: 'bold',
                          marginTop: '0.3rem',
                          color: ping.response_time_ms > 100 ? '#F44336' : ping.response_time_ms > 50 ? '#FF9800' : '#4CAF50'
                        }}>
                          {ping.response_time_ms} ms
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="details-grid" style={{
                    marginTop: '1rem',
                    backgroundColor: currentTheme.background,
                    padding: '0.5rem',
                    borderRadius: '4px',
                    border: `1px solid ${currentTheme.border}`
                  }}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.8rem', color: currentTheme.text }}>Min RTT</div>
                      <div style={{ fontSize: '1rem', fontWeight: 'bold', marginTop: '0.4rem' }}>{latestStatus.min_rtt} ms</div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.8rem', color: currentTheme.text }}>Avg RTT</div>
                      <div style={{ fontSize: '1rem', fontWeight: 'bold', marginTop: '0.4rem' }}>{latestStatus.avg_rtt} ms</div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.8rem', color: currentTheme.text }}>Max RTT</div>
                      <div style={{ fontSize: '1rem', fontWeight: 'bold', marginTop: '0.4rem' }}>{latestStatus.max_rtt} ms</div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.8rem', color: currentTheme.text }}>Packet Loss</div>
                      <div style={{ fontSize: '1rem', fontWeight: 'bold', marginTop: '0.4rem', color: latestStatus.packet_loss_percent > 0 ? '#F44336' : '#4CAF50' }}>
                        {latestStatus.packet_loss_percent}%
                      </div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.8rem', color: currentTheme.text }}>Transmitted</div>
                      <div style={{ fontSize: '1rem', fontWeight: 'bold', marginTop: '0.4rem' }}>{latestStatus.packets_transmitted}</div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.8rem', color: currentTheme.text }}>Received</div>
                      <div style={{ fontSize: '1rem', fontWeight: 'bold', marginTop: '0.4rem' }}>{latestStatus.packets_received}</div>
                    </div>
                  </div>
                </div>
              )
            ))}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer style={{
        backgroundColor: currentTheme.cardBackground,
        padding: '0.6rem',
        borderTop: `1px solid ${currentTheme.border}`,
        width: '100%',
        boxSizing: 'border-box',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '0.5rem',
        flexShrink: 0
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
    </>
  );
}
