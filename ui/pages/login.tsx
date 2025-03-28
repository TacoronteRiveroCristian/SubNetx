/**
 * Login page component with a form that validates admin credentials
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

  // Check if user is already authenticated on mount
  useEffect(() => {
    // If already authenticated, redirect to home
    if (localStorage.getItem('isAuthenticated') === 'true') {
      router.push('/');
    }
  }, [router]);

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    // Prevent default form submission behavior
    e.preventDefault();

    // Basic validation
    if (!email || !password) {
      // Set error message if validation fails
      setError('Please enter both email and password');
      return;
    }

    // Check if credentials match admin/admin
    if (email === 'admin' && password === 'admin') {
      // Set authentication in localStorage
      localStorage.setItem('isAuthenticated', 'true');

      // Clear any previous errors
      setError('');

      // Redirect to home page
      router.push('/');
    } else {
      // Set error for invalid credentials
      setError('Invalid credentials');
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
    </>
  );
}
