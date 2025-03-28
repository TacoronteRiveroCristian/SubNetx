/**
 * Login page component with a form that validates admin credentials
 * Sets authentication state in localStorage upon successful login
 * Features an interactive 3D background with grid and dots that follow mouse movement
 */
import Head from 'next/head'; // Import Head for document head modifications
import { useRouter } from 'next/router'; // Import useRouter for navigation
import { useEffect, useState } from 'react'; // Import useState and useEffect hooks
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
  const [mousePosition, setMousePosition] = useState({ x: 50, y: 50 });

  // Check if user is already authenticated on mount
  useEffect(() => {
    // If already authenticated, redirect to home
    if (localStorage.getItem('isAuthenticated') === 'true') {
      router.push('/');
    }

    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth) * 100,
        y: (e.clientY / window.innerHeight) * 100
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
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

        .background {
          position: fixed;
          top: 0;
          left: 0;
          width: 100vw;
          height: 100vh;
          background-color: ${theme.background};
          overflow: hidden;
          z-index: 0;
        }

        .network-grid {
          position: absolute;
          top: 50%;
          left: 50%;
          width: 200vw;
          height: 200vh;
          transform-origin: center;
          transform: translate(-50%, -50%)
                    perspective(2000px)
                    rotateX(${(mousePosition.y - 50) * 0.1}deg)
                    rotateY(${(mousePosition.x - 50) * 0.1}deg);
          background-image:
            radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, rgba(102, 187, 106, 0.15) 0%, transparent 35%),
            repeating-linear-gradient(rgba(255, 255, 255, 0.03) 0px, rgba(255, 255, 255, 0.03) 1px, transparent 1px, transparent 50px),
            repeating-linear-gradient(90deg, rgba(255, 255, 255, 0.03) 0px, rgba(255, 255, 255, 0.03) 1px, transparent 1px, transparent 50px);
          mask-image: radial-gradient(circle at center, black 30%, transparent 70%);
          -webkit-mask-image: radial-gradient(circle at center, black 30%, transparent 70%);
          transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          opacity: 0.8;
          will-change: transform;
          backface-visibility: hidden;
          transform-style: preserve-3d;
        }

        .network-dots {
          position: absolute;
          top: 50%;
          left: 50%;
          width: 200vw;
          height: 200vh;
          transform: translate(-50%, -50%);
          background-image:
            radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, rgba(102, 187, 106, 0.1) 0%, transparent 25%),
            radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 0.08) 2px, transparent 2.5px),
            radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
          background-size: 100% 100%, 28px 28px, 24px 24px;
          background-position: center;
          mask-image: radial-gradient(circle at center, black 40%, transparent 70%);
          -webkit-mask-image: radial-gradient(circle at center, black 40%, transparent 70%);
          animation: floatDots 120s linear infinite;
          opacity: 0.9;
          will-change: transform;
          backface-visibility: hidden;
          transform-style: preserve-3d;
        }

        @keyframes floatDots {
          from {
            transform: translate(-50%, -50%) rotate(0deg);
          }
          to {
            transform: translate(-50%, -50%) rotate(360deg);
          }
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
        <div className="background">
          <div className="network-grid"></div>
          <div className="network-dots"></div>
        </div>

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
