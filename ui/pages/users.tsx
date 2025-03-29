/**
 * User Management page component
 * Displays a list of users with their details and allows filtering and editing
 */
import Head from 'next/head';
import { useRouter } from 'next/router';
import React, { useEffect, useState } from 'react';
import BackgroundEffect from '../components/BackgroundEffect';
import Footer from '../components/Footer';

// Define User interface
interface User {
  id: number;
  username: string;
  role: 'admin' | 'viewer';  // Add role field
  createdAt: string;
  updatedAt: string;
}

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

export default function Users() {
  // Initialize router for navigation
  const router = useRouter();

  // State for users data and UI
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState<string | null>(null);

  // Add sort configuration state
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: 'ascending' | 'descending';
  } | null>(null);

  // Add new state for create user modal
  const [isCreatingUser, setIsCreatingUser] = useState(false);
  const [newUser, setNewUser] = useState({ username: '', password: '', confirmPassword: '', role: 'viewer' });
  const [deleteConfirmUser, setDeleteConfirmUser] = useState<User | null>(null);

  // Get current theme
  const currentTheme = themes[theme];

  // Check authentication on mount
  useEffect(() => {
    if (localStorage.getItem('isAuthenticated') !== 'true') {
      router.push('/login');
    }
  }, [router]);

  // Fetch users on mount
  useEffect(() => {
    fetchUsers();
  }, []);

  // Function to create default admin user
  const createDefaultAdminUser = async () => {
    try {
      const response = await fetch('/api/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          username: 'admin',
          password: 'admin',
          role: 'admin'
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      await fetchUsers();
    } catch (error) {
      console.error('Error creating default admin user:', error);
      setError(error instanceof Error ? error.message : 'Failed to create default admin user');
    }
  };

  // Function to fetch users
  const fetchUsers = async () => {
    try {
      const response = await fetch('/api/users', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
      });

      const contentType = response.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        throw new Error(`Expected JSON response but got ${contentType}`);
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const usersWithRoles = data.map((user: User) => ({
        ...user,
        role: user.role || 'viewer'
      }));

      // If no users exist, create default admin user
      if (usersWithRoles.length === 0) {
        await createDefaultAdminUser();
        return;
      }

      setUsers(usersWithRoles);
      setLoading(false);
      setError(null);
    } catch (error) {
      console.error('Error fetching users:', error);
      setError(error instanceof Error ? error.message : 'Failed to load users');
      setLoading(false);
    }
  };

  // Function to handle sort request
  const requestSort = (key: string) => {
    let direction: 'ascending' | 'descending' = 'ascending';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };

  // Function to sort users
  const sortedUsers = React.useMemo(() => {
    if (!sortConfig) return users;

    return [...users].sort((a, b) => {
      switch (sortConfig.key) {
        case 'id':
          return sortConfig.direction === 'ascending'
            ? a.id - b.id
            : b.id - a.id;
        case 'username':
          return sortConfig.direction === 'ascending'
            ? a.username.localeCompare(b.username)
            : b.username.localeCompare(a.username);
        case 'createdAt':
          return sortConfig.direction === 'ascending'
            ? new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
            : new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
        case 'updatedAt':
          return sortConfig.direction === 'ascending'
            ? new Date(a.updatedAt).getTime() - new Date(b.updatedAt).getTime()
            : new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
        case 'role':
          return sortConfig.direction === 'ascending'
            ? a.role.localeCompare(b.role)
            : b.role.localeCompare(a.role);
        default:
          return 0;
      }
    });
  }, [users, sortConfig]);

  // Add this function to check if the current user is admin
  const isCurrentUserAdmin = () => {
    // Get the current user's ID from localStorage or context
    const currentUserId = parseInt(localStorage.getItem('userId') || '0');
    return users.find(user => user.id === currentUserId)?.role === 'admin';
  };

  // Modify the handleDelete function to prevent admin deletion
  const handleDelete = async (userId: number) => {
    // Find the user to be deleted
    const userToDelete = users.find(u => u.id === userId);

    if (!userToDelete) {
      setError('User not found');
      return;
    }

    // Prevent deletion of admin user
    if (userToDelete.role === 'admin') {
      setError('Cannot delete admin user');
      setDeleteConfirmUser(null);
      return;
    }

    try {
      const response = await fetch(`/api/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Accept': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      const contentType = response.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        throw new Error(`Expected JSON response but got ${contentType}`);
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      await fetchUsers();
      setDeleteConfirmUser(null);
      setError(null);
    } catch (error) {
      console.error('Error deleting user:', error);
      setError(error instanceof Error ? error.message : 'Failed to delete user');
      setDeleteConfirmUser(null);
    }
  };

  // Modify the handleEdit function to handle role restrictions
  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;

    // Prevent changing admin role
    if (editingUser.role === 'admin') {
      const originalUser = users.find(u => u.id === editingUser.id);
      if (originalUser && originalUser.role !== editingUser.role) {
        setError('Cannot change admin role');
        return;
      }
    }

    if (newPassword) {
      if (newPassword !== confirmPassword) {
        setPasswordError('Passwords do not match');
        return;
      }
      if (newPassword.length < 8) {
        setPasswordError('Password must be at least 8 characters long');
        return;
      }
      setPasswordError(null);
    }

    try {
      const response = await fetch(`/api/users/${editingUser.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          username: editingUser.username,
          newPassword: newPassword || undefined,
          role: editingUser.role // Keep the role unchanged
        }),
      });

      const contentType = response.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        throw new Error(`Expected JSON response but got ${contentType}`);
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      await fetchUsers();
      setEditingUser(null);
      setNewPassword('');
      setConfirmPassword('');
      setPasswordError(null);
    } catch (error) {
      console.error('Error updating user:', error);
      setError(error instanceof Error ? error.message : 'Failed to update user');
    }
  };

  // Function to handle user creation
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null); // Reset password error

    if (newUser.password !== newUser.confirmPassword) {
      setPasswordError('Passwords do not match');
      return;
    }
    if (newUser.password.length < 8) {
      setPasswordError('Password must be at least 8 characters long');
      return;
    }

    // Check if username already exists
    const existingUser = users.find(user => user.username.toLowerCase() === newUser.username.toLowerCase());
    if (existingUser) {
      setPasswordError('Username already exists');
      return;
    }

    // Log the user data being sent
    console.log('Creating user with data:', {
      username: newUser.username,
      role: newUser.role
    });

    try {
      const response = await fetch('/api/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          username: newUser.username,
          password: newUser.password,
          role: newUser.role
        }),
      });

      const contentType = response.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        throw new Error(`Expected JSON response but got ${contentType}`);
      }

      if (!response.ok) {
        const errorData = await response.json();
        setPasswordError(errorData.message || 'Failed to create user');
        return;
      }

      // Log the response data
      const responseData = await response.json();
      console.log('User created successfully:', responseData);

      await fetchUsers();
      setIsCreatingUser(false);
      setNewUser({ username: '', password: '', confirmPassword: '', role: 'viewer' });
      setPasswordError(null);
    } catch (error) {
      console.error('Error creating user:', error);
      setPasswordError(error instanceof Error ? error.message : 'Failed to create user');
    }
  };

  return (
    <>
      <Head>
        <title>User Management | SubNetx</title>
        <meta name="description" content="Manage SubNetx users" />
        <link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons" />
        <style>{`
          body {
            margin: 0;
            padding: 0;
            background-color: ${currentTheme.background};
            color: ${currentTheme.text};
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
          }
          #__next {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
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
          .user-row:hover {
            background-color: ${currentTheme.tableRowHover} !important;
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
          padding: '1rem 1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: `1px solid ${currentTheme.border}`,
          position: 'sticky',
          top: 0,
          zIndex: 10
        }}>
          <h1 style={{
            margin: 0,
            fontSize: '1.75rem',
            color: currentTheme.text,
            fontWeight: 600,
            letterSpacing: '-0.5px'
          }}>
            User Management
          </h1>
          <button
            onClick={() => router.push('/dashboard')}
            style={{
              background: 'none',
              border: 'none',
              color: currentTheme.text,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              fontSize: '0.9rem',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = `${currentTheme.buttonHover}50`;
              e.currentTarget.style.transform = 'translateX(-4px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.transform = 'translateX(0)';
            }}
          >
            <span className="material-icons" style={{ fontSize: '20px' }}>
              arrow_back
            </span>
            Back to Dashboard
          </button>
        </div>

        <main style={{
          flex: 1,
          padding: '2rem',
          backgroundColor: 'transparent',
          color: currentTheme.text,
          position: 'relative',
          zIndex: 1
        }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              Loading users...
            </div>
          ) : error ? (
            <div style={{
              padding: '1rem',
              backgroundColor: currentTheme.errorBackground,
              color: '#F44336',
              borderRadius: '4px',
              marginBottom: '1rem'
            }}>
              {error}
            </div>
          ) : (
            <>
              <button
                onClick={() => setIsCreatingUser(true)}
                style={{
                  background: currentTheme.primary,
                  border: 'none',
                  color: '#fff',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '6px',
                  fontSize: '0.85rem',
                  marginBottom: '1rem',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <span className="material-icons" style={{ fontSize: '18px' }}>add</span>
                New User
              </button>

              <div style={{
                backgroundColor: `${currentTheme.cardBackground}99`,
                backdropFilter: 'blur(10px)',
                borderRadius: '8px',
                border: `1px solid ${currentTheme.border}`,
                overflow: 'hidden'
              }}>
                <table style={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  textAlign: 'left'
                }}>
                  <thead>
                    <tr style={{
                      backgroundColor: `${currentTheme.tableHeader}99`
                    }}>
                      <th
                        onClick={() => requestSort('id')}
                        style={{
                          padding: '1rem',
                          cursor: 'pointer',
                          userSelect: 'none',
                          backgroundColor: sortConfig?.key === 'id' ? `${currentTheme.primary}15` : 'transparent',
                          transition: 'all 0.2s ease'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = `${currentTheme.primary}25`;
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = sortConfig?.key === 'id' ? `${currentTheme.primary}15` : 'transparent';
                        }}
                      >
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}>
                          ID
                          <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}>
                            <span className="material-icons" style={{
                              fontSize: '16px',
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
                      <th
                        onClick={() => requestSort('username')}
                        style={{
                          padding: '1rem',
                          cursor: 'pointer',
                          userSelect: 'none',
                          backgroundColor: sortConfig?.key === 'username' ? `${currentTheme.primary}15` : 'transparent',
                          transition: 'all 0.2s ease'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = `${currentTheme.primary}25`;
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = sortConfig?.key === 'username' ? `${currentTheme.primary}15` : 'transparent';
                        }}
                      >
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}>
                          Username
                          <span className="material-icons" style={{
                            fontSize: '16px',
                            opacity: sortConfig?.key === 'username' ? 1 : 0.5,
                            color: currentTheme.primary
                          }}>
                            {sortConfig?.key === 'username'
                              ? (sortConfig.direction === 'ascending' ? 'arrow_upward' : 'arrow_downward')
                              : 'sort_by_alpha'
                            }
                          </span>
                        </div>
                      </th>
                      <th
                        onClick={() => requestSort('role')}
                        style={{
                          padding: '1rem',
                          cursor: 'pointer',
                          userSelect: 'none',
                          backgroundColor: sortConfig?.key === 'role' ? `${currentTheme.primary}15` : 'transparent',
                          transition: 'all 0.2s ease'
                        }}
                      >
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}>
                          Role
                          <span className="material-icons" style={{
                            fontSize: '16px',
                            opacity: sortConfig?.key === 'role' ? 1 : 0.5,
                            color: currentTheme.primary
                          }}>
                            {sortConfig?.key === 'role'
                              ? (sortConfig.direction === 'ascending' ? 'arrow_upward' : 'arrow_downward')
                              : 'sort'
                            }
                          </span>
                        </div>
                      </th>
                      <th
                        onClick={() => requestSort('createdAt')}
                        style={{
                          padding: '1rem',
                          cursor: 'pointer',
                          userSelect: 'none',
                          backgroundColor: sortConfig?.key === 'createdAt' ? `${currentTheme.primary}15` : 'transparent',
                          transition: 'all 0.2s ease'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = `${currentTheme.primary}25`;
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = sortConfig?.key === 'createdAt' ? `${currentTheme.primary}15` : 'transparent';
                        }}
                      >
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}>
                          Created At
                          <span className="material-icons" style={{
                            fontSize: '16px',
                            opacity: sortConfig?.key === 'createdAt' ? 1 : 0.5,
                            color: currentTheme.primary
                          }}>
                            {sortConfig?.key === 'createdAt'
                              ? (sortConfig.direction === 'ascending' ? 'arrow_upward' : 'arrow_downward')
                              : 'schedule'
                            }
                          </span>
                        </div>
                      </th>
                      <th
                        onClick={() => requestSort('updatedAt')}
                        style={{
                          padding: '1rem',
                          cursor: 'pointer',
                          userSelect: 'none',
                          backgroundColor: sortConfig?.key === 'updatedAt' ? `${currentTheme.primary}15` : 'transparent',
                          transition: 'all 0.2s ease'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = `${currentTheme.primary}25`;
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = sortConfig?.key === 'updatedAt' ? `${currentTheme.primary}15` : 'transparent';
                        }}
                      >
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}>
                          Last Updated
                          <span className="material-icons" style={{
                            fontSize: '16px',
                            opacity: sortConfig?.key === 'updatedAt' ? 1 : 0.5,
                            color: currentTheme.primary
                          }}>
                            {sortConfig?.key === 'updatedAt'
                              ? (sortConfig.direction === 'ascending' ? 'arrow_upward' : 'arrow_downward')
                              : 'schedule'
                            }
                          </span>
                        </div>
                      </th>
                      <th style={{ padding: '1rem' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedUsers.map(user => (
                      <tr
                        key={user.id}
                        className="user-row"
                        style={{
                          borderTop: `1px solid ${currentTheme.border}`
                        }}
                      >
                        <td style={{ padding: '1rem' }}>{user.id}</td>
                        <td style={{ padding: '1rem' }}>{user.username}</td>
                        <td style={{ padding: '1rem' }}>
                          <div style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            backgroundColor: (user.role === 'admin') ? `${currentTheme.primary}20` : `${currentTheme.secondary}20`,
                            color: (user.role === 'admin') ? currentTheme.primary : currentTheme.secondary,
                            fontSize: '0.85rem',
                            fontWeight: '500',
                            gap: '4px'
                          }}>
                            <span className="material-icons" style={{ fontSize: '16px' }}>
                              {(user.role === 'admin') ? 'admin_panel_settings' : 'visibility'}
                            </span>
                            {((user.role || 'viewer').charAt(0).toUpperCase() + (user.role || 'viewer').slice(1))}
                          </div>
                        </td>
                        <td style={{ padding: '1rem' }}>
                          {new Date(user.createdAt).toLocaleDateString()}
                        </td>
                        <td style={{ padding: '1rem' }}>
                          {new Date(user.updatedAt).toLocaleDateString()}
                        </td>
                        <td style={{ padding: '1rem' }}>
                          <div style={{
                            display: 'flex',
                            gap: '0.5rem'
                          }}>
                            <button
                              onClick={() => setEditingUser(user)}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: currentTheme.primary,
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.25rem',
                                padding: '0.5rem',
                                borderRadius: '4px',
                                transition: 'all 0.2s ease'
                              }}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.backgroundColor = `${currentTheme.buttonHover}50`;
                                e.currentTarget.style.transform = 'translateX(4px)';
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.backgroundColor = 'transparent';
                                e.currentTarget.style.transform = 'translateX(0)';
                              }}
                            >
                              <span className="material-icons" style={{ fontSize: '20px' }}>edit</span>
                              Edit
                            </button>
                            <button
                              onClick={() => setDeleteConfirmUser(user)}
                              disabled={users.length === 1 || user.role === 'admin'}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: users.length === 1 || user.role === 'admin' ? '#ff6b6b40' : '#F44336',
                                cursor: users.length === 1 || user.role === 'admin' ? 'not-allowed' : 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.25rem',
                                padding: '0.5rem',
                                borderRadius: '4px',
                                transition: 'all 0.2s ease',
                                opacity: users.length === 1 || user.role === 'admin' ? 0.8 : 1,
                                backgroundColor: users.length === 1 || user.role === 'admin' ? `${currentTheme.buttonHover}40` : 'transparent'
                              }}
                              onMouseEnter={(e) => {
                                if (users.length > 1 && user.role !== 'admin') {
                                  e.currentTarget.style.backgroundColor = `${currentTheme.buttonHover}50`;
                                  e.currentTarget.style.transform = 'translateX(4px)';
                                }
                              }}
                              onMouseLeave={(e) => {
                                if (users.length > 1 && user.role !== 'admin') {
                                  e.currentTarget.style.backgroundColor = 'transparent';
                                  e.currentTarget.style.transform = 'translateX(0)';
                                }
                              }}
                              title={user.role === 'admin' ? "Cannot delete admin user" : users.length === 1 ? "Cannot delete the last user" : "Delete user"}
                            >
                              <span className="material-icons" style={{ fontSize: '20px' }}>delete</span>
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </main>

        <Footer theme={currentTheme} />

        {/* Edit User Modal */}
        {editingUser && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 1000
          }}>
            <div style={{
              backgroundColor: `${currentTheme.cardBackground}99`,
              backdropFilter: 'blur(10px)',
              padding: '2rem',
              borderRadius: '8px',
              width: '90%',
              maxWidth: '500px',
              border: `1px solid ${currentTheme.border}`
            }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '1.5rem'
              }}>
                <h2 style={{ margin: 0, fontSize: '1.5rem', color: currentTheme.primary }}>Edit User</h2>
                <button
                  onClick={() => {
                    setEditingUser(null);
                    setNewPassword('');
                    setConfirmPassword('');
                    setPasswordError(null);
                  }}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: currentTheme.text,
                    cursor: 'pointer',
                    padding: '0.5rem',
                    borderRadius: '4px',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = `${currentTheme.buttonHover}50`;
                    e.currentTarget.style.transform = 'scale(1.1)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.transform = 'scale(1)';
                  }}
                >
                  <span className="material-icons">close</span>
                </button>
              </div>

              <form onSubmit={handleEdit}>
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{
                    display: 'block',
                    marginBottom: '0.5rem',
                    color: currentTheme.text
                  }}>
                    Username
                  </label>
                  <input
                    type="text"
                    value={editingUser.username}
                    onChange={(e) => setEditingUser({ ...editingUser, username: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      borderRadius: '4px',
                      border: `1px solid ${currentTheme.border}`,
                      backgroundColor: `${currentTheme.background}99`,
                      color: currentTheme.text,
                      fontSize: '1rem',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <label style={{
                    display: 'block',
                    marginBottom: '0.5rem',
                    color: currentTheme.text
                  }}>
                    New Password (leave blank to keep current)
                  </label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => {
                      setNewPassword(e.target.value);
                      setPasswordError(null);
                    }}
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      borderRadius: '4px',
                      border: `1px solid ${passwordError ? '#F44336' : currentTheme.border}`,
                      backgroundColor: `${currentTheme.background}99`,
                      color: currentTheme.text,
                      fontSize: '1rem',
                      boxSizing: 'border-box'
                    }}
                    placeholder="Enter new password"
                  />
                </div>

                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{
                    display: 'block',
                    marginBottom: '0.5rem',
                    color: currentTheme.text
                  }}>
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                      setPasswordError(null);
                    }}
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      borderRadius: '4px',
                      border: `1px solid ${passwordError ? '#F44336' : currentTheme.border}`,
                      backgroundColor: `${currentTheme.background}99`,
                      color: currentTheme.text,
                      fontSize: '1rem',
                      boxSizing: 'border-box'
                    }}
                    placeholder="Confirm new password"
                  />
                  {passwordError && (
                    <div style={{
                      color: '#F44336',
                      fontSize: '0.85rem',
                      marginTop: '0.5rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem'
                    }}>
                      <span className="material-icons" style={{ fontSize: '16px' }}>error</span>
                      {passwordError}
                    </div>
                  )}
                </div>

                <div style={{
                  display: 'flex',
                  gap: '1rem',
                  justifyContent: 'flex-end'
                }}>
                  <button
                    type="button"
                    onClick={() => {
                      setEditingUser(null);
                      setNewPassword('');
                      setConfirmPassword('');
                      setPasswordError(null);
                    }}
                    style={{
                      padding: '0.75rem 1.5rem',
                      borderRadius: '4px',
                      border: `1px solid ${currentTheme.border}`,
                      backgroundColor: 'transparent',
                      color: currentTheme.text,
                      cursor: 'pointer',
                      fontSize: '1rem',
                      transition: 'all 0.2s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = `${currentTheme.buttonHover}50`;
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    style={{
                      padding: '0.75rem 1.5rem',
                      borderRadius: '4px',
                      border: 'none',
                      backgroundColor: currentTheme.primary,
                      color: '#fff',
                      cursor: 'pointer',
                      fontSize: '1rem',
                      transition: 'all 0.2s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  >
                    Save Changes
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Create User Modal */}
        {isCreatingUser && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 1000
          }}>
            <div style={{
              backgroundColor: `${currentTheme.cardBackground}99`,
              backdropFilter: 'blur(10px)',
              padding: '2rem',
              borderRadius: '8px',
              width: '90%',
              maxWidth: '500px',
              border: `1px solid ${currentTheme.border}`
            }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '1.5rem'
              }}>
                <h2 style={{ margin: 0, fontSize: '1.5rem', color: currentTheme.primary }}>Create New User</h2>
                <button
                  onClick={() => {
                    setIsCreatingUser(false);
                    setNewUser({ username: '', password: '', confirmPassword: '', role: 'viewer' });
                    setPasswordError(null);
                  }}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: currentTheme.text,
                    cursor: 'pointer',
                    padding: '0.5rem',
                    borderRadius: '4px',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = `${currentTheme.buttonHover}50`;
                    e.currentTarget.style.transform = 'scale(1.1)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.transform = 'scale(1)';
                  }}
                >
                  <span className="material-icons">close</span>
                </button>
              </div>

              {passwordError && (
                <div style={{
                  color: '#F44336',
                  backgroundColor: `${currentTheme.errorBackground}80`,
                  padding: '0.75rem',
                  borderRadius: '4px',
                  marginBottom: '1rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontSize: '0.9rem'
                }}>
                  <span className="material-icons" style={{ fontSize: '20px' }}>error_outline</span>
                  {passwordError}
                </div>
              )}

              <form onSubmit={handleCreate}>
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{
                    display: 'block',
                    marginBottom: '0.5rem',
                    color: currentTheme.text
                  }}>
                    Username
                  </label>
                  <input
                    type="text"
                    value={newUser.username}
                    onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      borderRadius: '4px',
                      border: `1px solid ${passwordError === 'Username already exists' ? '#F44336' : currentTheme.border}`,
                      backgroundColor: `${currentTheme.background}99`,
                      color: currentTheme.text,
                      fontSize: '1rem',
                      boxSizing: 'border-box'
                    }}
                    required
                  />
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <label style={{
                    display: 'block',
                    marginBottom: '0.5rem',
                    color: currentTheme.text
                  }}>
                    Role
                  </label>
                  <select
                    value={newUser.role}
                    onChange={(e) => {
                      console.log('Role selected:', e.target.value);
                      setNewUser({ ...newUser, role: e.target.value as 'admin' | 'viewer' });
                    }}
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      borderRadius: '4px',
                      border: `1px solid ${currentTheme.border}`,
                      backgroundColor: `${currentTheme.background}99`,
                      color: currentTheme.text,
                      fontSize: '1rem',
                      boxSizing: 'border-box'
                    }}
                    required
                  >
                    <option value="viewer">Viewer</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <label style={{
                    display: 'block',
                    marginBottom: '0.5rem',
                    color: currentTheme.text
                  }}>
                    Password
                  </label>
                  <input
                    type="password"
                    value={newUser.password}
                    onChange={(e) => {
                      setNewUser({ ...newUser, password: e.target.value });
                      setPasswordError(null);
                    }}
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      borderRadius: '4px',
                      border: `1px solid ${passwordError && passwordError !== 'Username already exists' ? '#F44336' : currentTheme.border}`,
                      backgroundColor: `${currentTheme.background}99`,
                      color: currentTheme.text,
                      fontSize: '1rem',
                      boxSizing: 'border-box'
                    }}
                    required
                  />
                </div>

                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{
                    display: 'block',
                    marginBottom: '0.5rem',
                    color: currentTheme.text
                  }}>
                    Confirm Password
                  </label>
                  <input
                    type="password"
                    value={newUser.confirmPassword}
                    onChange={(e) => {
                      setNewUser({ ...newUser, confirmPassword: e.target.value });
                      setPasswordError(null);
                    }}
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      borderRadius: '4px',
                      border: `1px solid ${passwordError && passwordError !== 'Username already exists' ? '#F44336' : currentTheme.border}`,
                      backgroundColor: `${currentTheme.background}99`,
                      color: currentTheme.text,
                      fontSize: '1rem',
                      boxSizing: 'border-box'
                    }}
                    required
                  />
                </div>

                <div style={{
                  display: 'flex',
                  gap: '1rem',
                  justifyContent: 'flex-end'
                }}>
                  <button
                    type="button"
                    onClick={() => {
                      setIsCreatingUser(false);
                      setNewUser({ username: '', password: '', confirmPassword: '', role: 'viewer' });
                      setPasswordError(null);
                    }}
                    style={{
                      padding: '0.75rem 1.5rem',
                      borderRadius: '4px',
                      border: `1px solid ${currentTheme.border}`,
                      backgroundColor: 'transparent',
                      color: currentTheme.text,
                      cursor: 'pointer',
                      fontSize: '1rem',
                      transition: 'all 0.2s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = `${currentTheme.buttonHover}50`;
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    style={{
                      padding: '0.75rem 1.5rem',
                      borderRadius: '4px',
                      border: 'none',
                      backgroundColor: currentTheme.primary,
                      color: '#fff',
                      cursor: 'pointer',
                      fontSize: '1rem',
                      transition: 'all 0.2s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  >
                    Create User
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {deleteConfirmUser && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 1000
          }}>
            <div style={{
              backgroundColor: `${currentTheme.cardBackground}99`,
              backdropFilter: 'blur(10px)',
              padding: '2rem',
              borderRadius: '8px',
              width: '90%',
              maxWidth: '500px',
              border: `1px solid ${currentTheme.border}`
            }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '1.5rem'
              }}>
                <h2 style={{ margin: 0, fontSize: '1.5rem', color: '#F44336' }}>Delete User</h2>
                <button
                  onClick={() => setDeleteConfirmUser(null)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: currentTheme.text,
                    cursor: 'pointer',
                    padding: '0.5rem',
                    borderRadius: '4px',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = `${currentTheme.buttonHover}50`;
                    e.currentTarget.style.transform = 'scale(1.1)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.transform = 'scale(1)';
                  }}
                >
                  <span className="material-icons">close</span>
                </button>
              </div>

              <p style={{ color: currentTheme.text, marginBottom: '2rem' }}>
                Are you sure you want to delete the user "{deleteConfirmUser.username}"?
                {users.length <= 2 && (
                  <span style={{
                    display: 'block',
                    marginTop: '0.5rem',
                    color: '#F44336',
                    fontSize: '0.9rem',
                    fontStyle: 'italic'
                  }}>
                    Warning: After this deletion, only one user will remain in the system.
                  </span>
                )}
                This action cannot be undone.
              </p>

              <div style={{
                display: 'flex',
                gap: '1rem',
                justifyContent: 'flex-end'
              }}>
                <button
                  onClick={() => setDeleteConfirmUser(null)}
                  style={{
                    padding: '0.75rem 1.5rem',
                    borderRadius: '4px',
                    border: `1px solid ${currentTheme.border}`,
                    backgroundColor: 'transparent',
                    color: currentTheme.text,
                    cursor: 'pointer',
                    fontSize: '1rem',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = `${currentTheme.buttonHover}50`;
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDelete(deleteConfirmUser.id)}
                  style={{
                    padding: '0.75rem 1.5rem',
                    borderRadius: '4px',
                    border: 'none',
                    backgroundColor: '#F44336',
                    color: '#fff',
                    cursor: 'pointer',
                    fontSize: '1rem',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  Delete User
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
