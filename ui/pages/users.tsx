/**
 * User Management page component
 * Displays a list of users with their details and allows filtering and editing
 */
import Head from 'next/head';
import { useRouter } from 'next/router';
import React, { useEffect, useState } from 'react';
import BackgroundEffect from '../components/BackgroundEffect';
import Footer from '../components/Footer';
import Logo from '../components/Logo';

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
    const [successMessage, setSuccessMessage] = useState<string>('');
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
    // Agregar estado para el menú hamburguesa
    const [isHamburgerOpen, setIsHamburgerOpen] = useState(false);

    // Get current theme
    const currentTheme = themes[theme as keyof typeof themes];

    // Check authentication on mount
    useEffect(() => {
        if (localStorage.getItem('isAuthenticated') !== 'true') {
            router.push('/login');
        }
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

    // Function to check if current user is admin
    const isCurrentUserAdmin = () => {
        // Get the current user's ID from localStorage or context
        const currentUserId = parseInt(localStorage.getItem('userId') || '0');
        return users.find((user: User) => user.id === currentUserId)?.role === 'admin';
    };

    // Function to handle deletion confirmation
    const handleDeleteConfirmation = (user: User) => {
        // Don't allow deleting the last user or an admin
        if (users.length === 1 || user.role === 'admin') {
            setError(user.role === 'admin'
                ? 'Cannot delete admin users.'
                : 'Cannot delete the last user in the system.');
            return;
        }

        setDeleteConfirmUser(user);
    };

    // Function to handle the actual deletion
    const handleDeleteUser = async () => {
        if (!deleteConfirmUser) return;

        try {
            setError('');
            const response = await fetch(`/api/users/${deleteConfirmUser.id}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to delete user');
            }

            // Remove the user from the local state
            setUsers(users.filter((user: User) => user.id !== deleteConfirmUser.id));
            setDeleteConfirmUser(null);

            // Show success message
            setSuccessMessage('User deleted successfully');
            setTimeout(() => setSuccessMessage(''), 3000);

        } catch (err) {
            setError((err as Error).message);
        }
    };

    // Modify the handleEdit function to handle role restrictions
    const handleEdit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!editingUser) return;

        // Prevent changing admin role
        if (editingUser.role === 'admin') {
            const originalUser = users.find((u: User) => u.id === editingUser.id);
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
        const existingUser = users.find((user: User) => user.username.toLowerCase() === newUser.username.toLowerCase());
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

          /* Estilos para animaciones del menú hamburguesa */
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
                            onMouseEnter={(e: ReactMouseEvent) => {
                                e.currentTarget.style.opacity = '0.8';
                                e.currentTarget.style.transform = 'translateX(-4px)';
                            }}
                            onMouseLeave={(e: ReactMouseEvent) => {
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
                            onMouseEnter={(e: ReactMouseEvent) => {
                                e.currentTarget.style.backgroundColor = `${currentTheme.primary}25`;
                                e.currentTarget.style.transform = 'translateX(4px)';
                                e.currentTarget.style.boxShadow = `0 4px 12px ${currentTheme.primary}20`;
                            }}
                            onMouseLeave={(e: ReactMouseEvent) => {
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
                            onMouseEnter={(e: ReactMouseEvent) => {
                                e.currentTarget.style.backgroundColor = `${currentTheme.secondary}25`;
                                e.currentTarget.style.transform = 'translateX(4px)';
                                e.currentTarget.style.boxShadow = `0 4px 12px ${currentTheme.secondary}20`;
                            }}
                            onMouseLeave={(e: ReactMouseEvent) => {
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

                        {isCurrentUserAdmin() && (
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
                                onMouseEnter={(e: ReactMouseEvent) => {
                                    e.currentTarget.style.backgroundColor = `${currentTheme.secondary}25`;
                                    e.currentTarget.style.transform = 'translateX(4px)';
                                    e.currentTarget.style.boxShadow = `0 4px 12px ${currentTheme.secondary}20`;
                                }}
                                onMouseLeave={(e: ReactMouseEvent) => {
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
                        )}

                        <button
                            onClick={() => {
                                const newTheme = theme === 'light' ? 'dark' : 'light';
                                // Save theme preference to localStorage
                                localStorage.setItem('appTheme', newTheme);
                                // Update state
                                setTheme(newTheme);
                                // Update document attribute for CSS
                                document.documentElement.setAttribute('data-theme', newTheme);
                            }}
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
                            onMouseEnter={(e: ReactMouseEvent) => {
                                e.currentTarget.style.backgroundColor = `${currentTheme.primary}25`;
                                e.currentTarget.style.transform = 'translateX(4px)';
                                e.currentTarget.style.boxShadow = `0 4px 12px ${currentTheme.primary}20`;
                            }}
                            onMouseLeave={(e: ReactMouseEvent) => {
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
                        onMouseEnter={(e: ReactMouseEvent) => {
                            e.currentTarget.style.backgroundColor = `${currentTheme.errorBackground}50`;
                            e.currentTarget.style.transform = 'translateX(4px)';
                            e.currentTarget.style.boxShadow = '0 4px 12px rgba(244,67,54,0.2)';
                        }}
                        onMouseLeave={(e: ReactMouseEvent) => {
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

                <main style={{
                    flex: 1,
                    padding: '2rem',
                    backgroundColor: 'transparent',
                    color: currentTheme.text,
                    position: 'relative',
                    zIndex: 1
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
                                color: currentTheme.primary,
                                // marginBottom: '2px'
                            }}>
                                people
                            </span>
                            <span style={{ lineHeight: 1 }}>User Management</span>
                        </h1>
                    </div>

                    {successMessage && (
                        <div style={{
                            padding: '1rem',
                            backgroundColor: '#4CAF5020',
                            color: '#4CAF50',
                            borderRadius: '4px',
                            marginBottom: '1rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px'
                        }}>
                            <span className="material-icons" style={{ fontSize: '20px' }}>check_circle</span>
                            {successMessage}
                        </div>
                    )}

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
                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                                gap: '1.5rem',
                                marginBottom: '2rem'
                            }}>
                                <button
                                    onClick={() => setIsCreatingUser(true)}
                                    className="user-action-button"
                                    style={{
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        padding: '1.5rem',
                                        borderRadius: '12px',
                                        border: `1px solid #FF980060`,
                                        backgroundColor: `#FF980010`,
                                        color: currentTheme.text,
                                        transition: 'all 0.3s ease',
                                        cursor: 'pointer',
                                        gap: '12px',
                                        height: '120px',
                                        width: '100%'
                                    }}
                                    onMouseEnter={(e: ReactMouseEvent) => {
                                        e.currentTarget.style.transform = 'translateY(-4px)';
                                        e.currentTarget.style.boxShadow = '0 6px 12px rgba(0,0,0,0.15)';
                                        e.currentTarget.style.backgroundColor = '#FF980020';
                                    }}
                                    onMouseLeave={(e: ReactMouseEvent) => {
                                        e.currentTarget.style.transform = 'translateY(0)';
                                        e.currentTarget.style.boxShadow = 'none';
                                        e.currentTarget.style.backgroundColor = '#FF980010';
                                    }}
                                >
                                    <span className="material-icons" style={{ fontSize: '36px', color: '#FF9800' }}>
                                        person_add
                                    </span>
                                    <div style={{ fontWeight: '500', fontSize: '1.1rem' }}>
                                        Create New User
                                    </div>
                                    <div style={{ fontSize: '0.85rem', opacity: 0.8, textAlign: 'center' }}>
                                        Add a new user to the system
                                    </div>
                                </button>
                            </div>

                            <div style={{
                                backgroundColor: `${currentTheme.cardBackground}99`,
                                backdropFilter: 'blur(10px)',
                                borderRadius: '8px',
                                border: `1px solid ${currentTheme.border}`,
                                overflow: 'hidden'
                            }}>
                                <div style={{
                                    padding: '1rem',
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    borderBottom: `1px solid ${currentTheme.border}`,
                                    backgroundColor: `${currentTheme.cardBackground}`
                                }}>
                                    <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <span className="material-icons" style={{ color: currentTheme.primary, fontSize: '20px' }}>
                                            format_list_bulleted
                                        </span>
                                        User List
                                    </h3>
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                            <span style={{ fontSize: '0.85rem', opacity: 0.8 }}>Total:</span>
                                            <span style={{ fontWeight: '500' }}>{users.length}</span>
                                        </div>
                                    </div>
                                </div>
                                {users.length === 0 ? (
                                    <div style={{
                                        padding: '2rem',
                                        textAlign: 'center',
                                        color: `${currentTheme.secondary}`
                                    }}>
                                        No users found
                                    </div>
                                ) : (
                                    <div className="user-table-container" style={{ overflowX: 'auto' }}>
                                        <table className="user-table" style={{
                                            width: '100%',
                                            borderCollapse: 'collapse',
                                            color: currentTheme.text
                                        }}>
                                            <thead>
                                                <tr style={{
                                                    borderBottom: `1px solid ${currentTheme.border}`,
                                                    backgroundColor: `${currentTheme.cardBackground}`
                                                }}>
                                                    <th
                                                        onClick={() => requestSort('username')}
                                                        style={{
                                                            textAlign: 'left',
                                                            padding: '0.75rem 1rem',
                                                            fontSize: '0.9rem',
                                                            fontWeight: 500,
                                                            cursor: 'pointer',
                                                            transition: 'all 0.2s ease'
                                                        }}
                                                        onMouseEnter={(e: ReactMouseEvent) => {
                                                            e.currentTarget.style.backgroundColor = `${currentTheme.primary}15`;
                                                        }}
                                                        onMouseLeave={(e: ReactMouseEvent) => {
                                                            e.currentTarget.style.backgroundColor = sortConfig?.key === 'username' ? `${currentTheme.primary}15` : 'transparent';
                                                        }}
                                                    >
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                            Username
                                                            <span className="material-icons" style={{
                                                                fontSize: '16px',
                                                                opacity: sortConfig?.key === 'username' ? 1 : 0.5,
                                                                color: currentTheme.primary
                                                            }}>
                                                                {sortConfig?.key === 'username'
                                                                    ? (sortConfig.direction === 'ascending' ? 'arrow_upward' : 'arrow_downward')
                                                                    : 'person'
                                                                }
                                                            </span>
                                                        </div>
                                                    </th>
                                                    <th
                                                        onClick={() => requestSort('role')}
                                                        style={{
                                                            textAlign: 'left',
                                                            padding: '0.75rem 1rem',
                                                            fontSize: '0.9rem',
                                                            fontWeight: 500,
                                                            cursor: 'pointer',
                                                            transition: 'all 0.2s ease'
                                                        }}
                                                        onMouseEnter={(e: ReactMouseEvent) => {
                                                            e.currentTarget.style.backgroundColor = `${currentTheme.primary}15`;
                                                        }}
                                                        onMouseLeave={(e: ReactMouseEvent) => {
                                                            e.currentTarget.style.backgroundColor = sortConfig?.key === 'role' ? `${currentTheme.primary}15` : 'transparent';
                                                        }}
                                                    >
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                            Role
                                                            <span className="material-icons" style={{
                                                                fontSize: '16px',
                                                                opacity: sortConfig?.key === 'role' ? 1 : 0.5,
                                                                color: currentTheme.primary
                                                            }}>
                                                                {sortConfig?.key === 'role'
                                                                    ? (sortConfig.direction === 'ascending' ? 'arrow_upward' : 'arrow_downward')
                                                                    : 'admin_panel_settings'
                                                                }
                                                            </span>
                                                        </div>
                                                    </th>
                                                    <th
                                                        onClick={() => requestSort('createdAt')}
                                                        style={{
                                                            textAlign: 'left',
                                                            padding: '0.75rem 1rem',
                                                            fontSize: '0.9rem',
                                                            fontWeight: 500,
                                                            cursor: 'pointer',
                                                            transition: 'all 0.2s ease'
                                                        }}
                                                        onMouseEnter={(e: ReactMouseEvent) => {
                                                            e.currentTarget.style.backgroundColor = `${currentTheme.primary}15`;
                                                        }}
                                                        onMouseLeave={(e: ReactMouseEvent) => {
                                                            e.currentTarget.style.backgroundColor = sortConfig?.key === 'createdAt' ? `${currentTheme.primary}15` : 'transparent';
                                                        }}
                                                    >
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                            Created At
                                                            <span className="material-icons" style={{
                                                                fontSize: '16px',
                                                                opacity: sortConfig?.key === 'createdAt' ? 1 : 0.5,
                                                                color: currentTheme.primary
                                                            }}>
                                                                {sortConfig?.key === 'createdAt'
                                                                    ? (sortConfig.direction === 'ascending' ? 'arrow_upward' : 'arrow_downward')
                                                                    : 'event'
                                                                }
                                                            </span>
                                                        </div>
                                                    </th>
                                                    <th
                                                        onClick={() => requestSort('updatedAt')}
                                                        style={{
                                                            textAlign: 'left',
                                                            padding: '0.75rem 1rem',
                                                            fontSize: '0.9rem',
                                                            fontWeight: 500,
                                                            cursor: 'pointer',
                                                            transition: 'all 0.2s ease'
                                                        }}
                                                        onMouseEnter={(e: ReactMouseEvent) => {
                                                            e.currentTarget.style.backgroundColor = `${currentTheme.primary}15`;
                                                        }}
                                                        onMouseLeave={(e: ReactMouseEvent) => {
                                                            e.currentTarget.style.backgroundColor = sortConfig?.key === 'updatedAt' ? `${currentTheme.primary}15` : 'transparent';
                                                        }}
                                                    >
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                            Last Updated
                                                            <span className="material-icons" style={{
                                                                fontSize: '16px',
                                                                opacity: sortConfig?.key === 'updatedAt' ? 1 : 0.5,
                                                                color: currentTheme.primary
                                                            }}>
                                                                {sortConfig?.key === 'updatedAt'
                                                                    ? (sortConfig.direction === 'ascending' ? 'arrow_upward' : 'arrow_downward')
                                                                    : 'update'
                                                                }
                                                            </span>
                                                        </div>
                                                    </th>
                                                    <th style={{
                                                        textAlign: 'center',
                                                        padding: '0.75rem 1rem',
                                                        fontSize: '0.9rem',
                                                        fontWeight: 500
                                                    }}>Actions</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {sortedUsers.map((user: User) => (
                                                    <tr key={user.username} style={{
                                                        borderBottom: `1px solid ${currentTheme.border}`,
                                                        backgroundColor: `${currentTheme.cardBackground}80`,
                                                        transition: 'background-color 0.2s ease'
                                                    }}
                                                        onMouseEnter={(e: ReactMouseEvent) => {
                                                            e.currentTarget.style.backgroundColor = `${currentTheme.tableRowHover}`;
                                                        }}
                                                        onMouseLeave={(e: ReactMouseEvent) => {
                                                            e.currentTarget.style.backgroundColor = `${currentTheme.cardBackground}80`;
                                                        }}>
                                                        <td style={{ padding: '0.75rem 1rem' }}>
                                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                                <span className="material-icons" style={{
                                                                    color: user.role === 'admin' ? currentTheme.secondary : currentTheme.primary,
                                                                    fontSize: '20px'
                                                                }}>
                                                                    {user.role === 'admin' ? 'admin_panel_settings' : 'person'}
                                                                </span>
                                                                {user.username}
                                                            </div>
                                                        </td>
                                                        <td style={{ padding: '0.75rem 1rem' }}>
                                                            <span style={{
                                                                display: 'inline-block',
                                                                padding: '4px 8px',
                                                                borderRadius: '4px',
                                                                fontSize: '0.75rem',
                                                                backgroundColor: user.role === 'admin' ? `${currentTheme.secondary}20` : `${currentTheme.primary}20`,
                                                                color: user.role === 'admin' ? currentTheme.secondary : currentTheme.primary,
                                                                fontWeight: 500
                                                            }}>
                                                                {user.role === 'admin' ? 'Admin' : 'User'}
                                                            </span>
                                                        </td>
                                                        <td style={{ padding: '0.75rem 1rem', fontSize: '0.9rem' }}>
                                                            {new Date(user.createdAt).toLocaleDateString()}
                                                        </td>
                                                        <td style={{ padding: '0.75rem 1rem', fontSize: '0.9rem' }}>
                                                            {new Date(user.updatedAt).toLocaleDateString()}
                                                        </td>
                                                        <td style={{
                                                            padding: '0.75rem 1rem',
                                                            textAlign: 'center'
                                                        }}>
                                                            <div style={{ display: 'flex', justifyContent: 'center', gap: '8px' }}>
                                                                <button
                                                                    onClick={() => setEditingUser(user)}
                                                                    style={{
                                                                        backgroundColor: 'transparent',
                                                                        border: 'none',
                                                                        padding: '6px',
                                                                        borderRadius: '4px',
                                                                        cursor: 'pointer',
                                                                        color: currentTheme.primary,
                                                                        transition: 'all 0.2s ease'
                                                                    }}
                                                                    onMouseEnter={(e: ReactMouseEvent) => {
                                                                        e.currentTarget.style.backgroundColor = `${currentTheme.primary}20`;
                                                                    }}
                                                                    onMouseLeave={(e: ReactMouseEvent) => {
                                                                        e.currentTarget.style.backgroundColor = 'transparent';
                                                                    }}
                                                                >
                                                                    <span className="material-icons" style={{ fontSize: '20px' }}>edit</span>
                                                                </button>
                                                                <button
                                                                    onClick={() => handleDeleteConfirmation(user)}
                                                                    disabled={users.length === 1 || user.role === 'admin'}
                                                                    style={{
                                                                        backgroundColor: 'transparent',
                                                                        border: 'none',
                                                                        padding: '6px',
                                                                        borderRadius: '4px',
                                                                        cursor: users.length === 1 || user.role === 'admin' ? 'not-allowed' : 'pointer',
                                                                        color: users.length === 1 || user.role === 'admin' ? '#F4433640' : '#F44336',
                                                                        opacity: users.length === 1 || user.role === 'admin' ? 0.5 : 1,
                                                                        transition: 'all 0.2s ease'
                                                                    }}
                                                                    onMouseEnter={(e: ReactMouseEvent) => {
                                                                        if (users.length > 1 && user.role !== 'admin') {
                                                                            e.currentTarget.style.backgroundColor = `${currentTheme.errorBackground}40`;
                                                                        }
                                                                    }}
                                                                    onMouseLeave={(e: ReactMouseEvent) => {
                                                                        e.currentTarget.style.backgroundColor = 'transparent';
                                                                    }}
                                                                    title={user.role === 'admin' ? "Cannot delete admin user" : users.length === 1 ? "Cannot delete the last user" : "Delete user"}
                                                                >
                                                                    <span className="material-icons" style={{ fontSize: '20px' }}>delete</span>
                                                                </button>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
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
                                    onMouseEnter={(e: ReactMouseEvent) => {
                                        e.currentTarget.style.backgroundColor = `${currentTheme.buttonHover}50`;
                                        e.currentTarget.style.transform = 'scale(1.1)';
                                    }}
                                    onMouseLeave={(e: ReactMouseEvent) => {
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
                                        onChange={(e: ReactChangeEvent) => setEditingUser({ ...editingUser, username: e.target.value })}
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
                                        onChange={(e: ReactChangeEvent) => {
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
                                        onChange={(e: ReactChangeEvent) => {
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
                                        onMouseEnter={(e: ReactMouseEvent) => {
                                            e.currentTarget.style.backgroundColor = `${currentTheme.buttonHover}50`;
                                        }}
                                        onMouseLeave={(e: ReactMouseEvent) => {
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
                                        onMouseEnter={(e: ReactMouseEvent) => {
                                            e.currentTarget.style.transform = 'translateY(-2px)';
                                            e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                                        }}
                                        onMouseLeave={(e: ReactMouseEvent) => {
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
                                    onMouseEnter={(e: ReactMouseEvent) => {
                                        e.currentTarget.style.backgroundColor = `${currentTheme.buttonHover}50`;
                                        e.currentTarget.style.transform = 'scale(1.1)';
                                    }}
                                    onMouseLeave={(e: ReactMouseEvent) => {
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
                                        onChange={(e: ReactChangeEvent) => setNewUser({ ...newUser, username: e.target.value })}
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
                                        onChange={(e: ReactChangeEvent) => {
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
                                        onChange={(e: ReactChangeEvent) => {
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
                                        onChange={(e: ReactChangeEvent) => {
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
                                        onMouseEnter={(e: ReactMouseEvent) => {
                                            e.currentTarget.style.backgroundColor = `${currentTheme.buttonHover}50`;
                                        }}
                                        onMouseLeave={(e: ReactMouseEvent) => {
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
                                        onMouseEnter={(e: ReactMouseEvent) => {
                                            e.currentTarget.style.transform = 'translateY(-2px)';
                                            e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                                        }}
                                        onMouseLeave={(e: ReactMouseEvent) => {
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
                                    onMouseEnter={(e: ReactMouseEvent) => {
                                        e.currentTarget.style.backgroundColor = `${currentTheme.buttonHover}50`;
                                        e.currentTarget.style.transform = 'scale(1.1)';
                                    }}
                                    onMouseLeave={(e: ReactMouseEvent) => {
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
                                    onMouseEnter={(e: ReactMouseEvent) => {
                                        e.currentTarget.style.backgroundColor = `${currentTheme.buttonHover}50`;
                                    }}
                                    onMouseLeave={(e: ReactMouseEvent) => {
                                        e.currentTarget.style.backgroundColor = 'transparent';
                                    }}
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={() => handleDeleteUser()}
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
                                    onMouseEnter={(e: ReactMouseEvent) => {
                                        e.currentTarget.style.transform = 'translateY(-2px)';
                                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                                    }}
                                    onMouseLeave={(e: ReactMouseEvent) => {
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
