// pages/index.tsx
import Head from 'next/head';
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
  },
};

export default function Home() {
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
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  // State to track if settings panel is open
  const [showSettings, setShowSettings] = useState(false);
  // State to track refresh interval
  const [refreshInterval, setRefreshInterval] = useState(10);
  // State to track when data is being updated
  const [isUpdating, setIsUpdating] = useState(false);
  // Ref to store the interval ID for cleanup
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

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

  return (
    <>
      <Head>
        <title>Target Monitor</title>
        <meta name="description" content="Monitor network targets in real-time" />
        <style>{`
          body {
            margin: 0;
            padding: 0;
            background-color: ${currentTheme.background};
            color: ${currentTheme.text};
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
        `}</style>
      </Head>

      <main style={{
        padding: '2rem',
        fontFamily: 'sans-serif',
        backgroundColor: currentTheme.background,
        color: currentTheme.text,
        minHeight: '100vh',
        width: '100%',
        boxSizing: 'border-box'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <h1 style={{ margin: 0 }}>Target Monitor</h1>
          <div>
            {/* Settings button */}
            <button
              onClick={() => setShowSettings(!showSettings)}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: currentTheme.secondary,
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                marginRight: '1rem'
              }}
            >
              Settings
            </button>
            {/* Theme toggle button */}
            <button
              onClick={toggleTheme}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: currentTheme.primary,
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              {theme === 'light' ? '🌙 Dark Mode' : '☀️ Light Mode'}
            </button>
          </div>
        </div>

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

        <div style={{ marginBottom: '1rem' }}>
          {/* Button to toggle real-time monitoring */}
          <button
            onClick={toggleMonitoring}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: isMonitoring ? '#F44336' : currentTheme.primary,
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              marginRight: '1rem'
            }}
            disabled={loading}
          >
            {loading ? 'Loading...' : isMonitoring ? 'Stop Monitoring' : 'Start Real-time Monitoring'}
          </button>

          {/* Button to manually fetch data */}
          {!isMonitoring && (
            <button
              onClick={fetchTargets}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: currentTheme.secondary,
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Fetch Data Manually'}
            </button>
          )}
        </div>

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
            <h2>Monitored Targets</h2>
            <table style={{
              borderCollapse: 'collapse',
              width: '100%',
              marginBottom: '2rem',
              backgroundColor: currentTheme.background
            }}>
              <thead>
                <tr style={{ backgroundColor: currentTheme.tableHeader }}>
                  <th style={{ border: `1px solid ${currentTheme.border}`, padding: '8px', textAlign: 'left' }}>ID</th>
                  <th style={{ border: `1px solid ${currentTheme.border}`, padding: '8px', textAlign: 'left' }}>Target</th>
                  <th style={{ border: `1px solid ${currentTheme.border}`, padding: '8px', textAlign: 'left' }}>Status</th>
                  <th style={{ border: `1px solid ${currentTheme.border}`, padding: '8px', textAlign: 'left' }}>Last Updated</th>
                  <th style={{ border: `1px solid ${currentTheme.border}`, padding: '8px', textAlign: 'left' }}>Connection Quality</th>
                  <th style={{ border: `1px solid ${currentTheme.border}`, padding: '8px', textAlign: 'left' }}>Packet Loss</th>
                  <th style={{ border: `1px solid ${currentTheme.border}`, padding: '8px', textAlign: 'left' }}>Avg RTT (ms)</th>
                </tr>
              </thead>
              <tbody>
                {targetsWithStatus.map(({ target, latestStatus }) => (
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

        {/* Show a message when no targets are available */}
        {!loading && targetsWithStatus.length === 0 && !error && (
          <p>No targets available. Click the button above to start monitoring.</p>
        )}
      </main>
    </>
  );
}
