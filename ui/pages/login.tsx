/**
 * Login page component with a form that validates credentials
 * Sets authentication state in localStorage upon successful login
 * Features an interactive 3D background with grid and dots that follow mouse movement
 */
import Head from 'next/head'; // Import Head for document head modifications
import { useRouter } from 'next/router'; // Import useRouter for navigation
import { useEffect, useState } from 'react'; // Import useState and useEffect hooks
import BackgroundEffect from '../components/BackgroundEffect'; // Import BackgroundEffect component
import Footer from '../components/Footer';
import Logo from '../components/Logo';

// Define the Login component
export default function Login() {
  // Initialize router for navigation
  const router = useRouter();

  // State for form inputs
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  // State for security warning modal
  const [showSecurityWarning, setShowSecurityWarning] = useState(false);
  // State for password change form
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');

  // Check if user is already authenticated on mount
  useEffect(() => {
    // If already authenticated, redirect to home
    if (localStorage.getItem('isAuthenticated') === 'true') {
      router.push('/');
    }
  }, [router]);

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
        // Call the login API
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: email,
                password: password
            }),
        });

        const data = await response.json();

        if (response.ok) {
            // Set authentication in localStorage
            localStorage.setItem('isAuthenticated', 'true');
            // Store user data
            localStorage.setItem('userId', data.user.id.toString());
            localStorage.setItem('userRole', data.user.role);
            // Clear any previous errors
            setError('');

            // If using default credentials, show security warning
            if (data.isDefaultCredentials) {
                setShowSecurityWarning(true);
            } else {
                // Redirect to dashboard if not using default credentials
                router.push('/dashboard');
            }
        } else {
            setError(data.message || 'Invalid credentials');
        }
    } catch (error) {
        console.error('Login error:', error);
        setError('An error occurred during login');
    }
  };

  // Handle password change
  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      setPasswordError('Passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setPasswordError('Password must be at least 8 characters long');
      return;
    }

    try {
      const response = await fetch('/api/auth/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: 'admin',
          currentPassword: 'admin',
          newPassword,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setPasswordError(data.message);
        return;
      }

      // Show success message and indicate if user was promoted to admin
      const successMessage = data.isAdmin
        ? 'Password changed successfully! You are now an admin user.'
        : 'Password changed successfully!';

      setShowSecurityWarning(false);
      setNewPassword('');
      setConfirmPassword('');
      setPasswordError(null);

      // Show success message
      alert(successMessage);

      // Redirect to dashboard
      router.push('/dashboard');
    } catch (error) {
      console.error('Error changing password:', error);
      setPasswordError('Failed to change password. Please try again.');
    }
  };

  // Define a theme style similar to the main app
  const theme = {
    background: '#1a1a1a',
    text: '#ffffff',
    primary: '#66bb6a',
    secondary: '#42a5f5',
    border: '#333333',
    cardBackground: '#2d2d2d',
  };

  return (
    <>
      <Head>
        <title>Login | SubNetx</title>
        <meta name="description" content="Login to SubNetx dashboard" />
        <link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons" />
      </Head>

      <style jsx global>{`
        body {
          margin: 0;
          padding: 0;
          background-color: ${theme.background};
          color: ${theme.text};
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
          overflow-x: hidden;
          min-height: 100vh;
        }

        #__next {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
        }

        .page-wrapper {
          display: flex;
          flex-direction: column;
          min-height: 100vh;
          position: relative;
          z-index: 1;
        }

        .content {
          position: relative;
          z-index: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          flex: 1;
          width: 100%;
          box-sizing: border-box;
          padding-bottom: 1rem;
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
          background-color: ${theme.cardBackground};
          padding: 2rem;
          border-radius: 8px;
          width: 90%;
          max-width: 500px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .modal-header {
          display: flex;
          align-items: center;
          margin-bottom: 1.5rem;
        }

        .modal-title {
          margin: 0;
          color: #F44336;
          font-size: 1.5rem;
        }

        .modal-icon {
          margin-right: 0.5rem;
          color: #F44336;
        }
      `}</style>

      <div className="page-wrapper">
        <BackgroundEffect theme={{ background: theme.background, primary: theme.primary }} />

        <main className="content">
          <div style={{
            backgroundColor: theme.cardBackground,
            padding: '2rem',
            borderRadius: '8px',
            width: '100%',
            maxWidth: '400px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            margin: 'auto'
          }}>
            <Logo theme={theme} size="medium" />

            {error && (
              <div style={{
                backgroundColor: '#FFEBEE',
                color: '#D32F2F',
                padding: '0.75rem',
                marginBottom: '1rem',
                borderRadius: '4px',
                fontWeight: 500
              }}>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{
                  display: 'block',
                  marginBottom: '0.5rem',
                  fontWeight: 500
                }}>
                  Username
                </label>
                <input
                  type="text"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    borderRadius: '4px',
                    border: `1px solid ${theme.border}`,
                    backgroundColor: theme.background,
                    color: theme.text,
                    fontSize: '1rem',
                    height: '48px',
                    boxSizing: 'border-box'
                  }}
                  placeholder="Enter admin username"
                />
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{
                  display: 'block',
                  marginBottom: '0.5rem',
                  fontWeight: 500
                }}>
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    borderRadius: '4px',
                    border: `1px solid ${theme.border}`,
                    backgroundColor: theme.background,
                    color: theme.text,
                    fontSize: '1rem',
                    height: '48px',
                    boxSizing: 'border-box'
                  }}
                  placeholder="Enter password"
                />
              </div>

              <button
                type="submit"
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  backgroundColor: theme.primary,
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '1rem',
                  fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'background-color 0.2s',
                  height: '48px'
                }}
              >
                Log In
              </button>
            </form>
          </div>
        </main>

        <Footer theme={theme} />
      </div>

      {/* Security Warning Modal */}
      {showSecurityWarning && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <span className="material-icons modal-icon">warning</span>
              <h2 className="modal-title">Security Warning</h2>
            </div>
            <p style={{ marginBottom: '1.5rem', lineHeight: '1.5' }}>
              You are currently using the default credentials (admin/admin). For security reasons, please change your password immediately.
            </p>
            <form onSubmit={handlePasswordChange}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{
                  display: 'block',
                  marginBottom: '0.5rem',
                  fontWeight: 500
                }}>
                  New Password
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    borderRadius: '4px',
                    border: `1px solid ${theme.border}`,
                    backgroundColor: theme.background,
                    color: theme.text,
                    fontSize: '1rem',
                    height: '48px',
                    boxSizing: 'border-box'
                  }}
                  placeholder="Enter new password"
                />
              </div>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{
                  display: 'block',
                  marginBottom: '0.5rem',
                  fontWeight: 500
                }}>
                  Confirm New Password
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    borderRadius: '4px',
                    border: `1px solid ${theme.border}`,
                    backgroundColor: theme.background,
                    color: theme.text,
                    fontSize: '1rem',
                    height: '48px',
                    boxSizing: 'border-box'
                  }}
                  placeholder="Confirm new password"
                />
              </div>
              {passwordError && (
                <div style={{
                  backgroundColor: '#FFEBEE',
                  color: '#D32F2F',
                  padding: '0.75rem',
                  marginBottom: '1rem',
                  borderRadius: '4px',
                  fontWeight: 500
                }}>
                  {passwordError}
                </div>
              )}
              <button
                type="submit"
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  backgroundColor: theme.primary,
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '1rem',
                  fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'background-color 0.2s',
                  height: '48px'
                }}
              >
                Change Password
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
