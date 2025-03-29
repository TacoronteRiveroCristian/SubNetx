/**
 * Custom App component that wraps all pages
 * Provides global layouts and handles page transitions
 */
import { AppProps } from 'next/app'; // Import AppProps type for typing
import Head from 'next/head';
import { useRouter } from 'next/router'; // Import useRouter for navigation tracking
import { useEffect, useState } from 'react'; // Import hooks for state and side effects

// Define the custom App component with proper typing
export default function App({ Component, pageProps }: AppProps) {
  // Initialize router
  const router = useRouter();

  // State to track if the user is authenticated
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  // Add this state to prevent redirect loops
  const [isRedirecting, setIsRedirecting] = useState(false);

  // Effect to handle route protection
  useEffect(() => {
    // Skip the check if already redirecting to prevent loops
    if (isRedirecting) return;

    const checkAuth = async () => {
      try {
        const response = await fetch('/api/auth/verify', {
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Not authenticated');
        }

        const data = await response.json();

        // Siempre establecemos el estado de isAuthenticated en localStorage
        localStorage.setItem('userRole', data.user.role);

        // Cuando navegamos al dashboard, aseguramos que no haya datos persistentes
        // que puedan interferir con la inicialización limpia
        if (router.pathname === '/dashboard') {
          // Guardar solo lo esencial para la autenticación
          localStorage.setItem('isAuthenticated', 'true');
          localStorage.setItem('userRole', data.user.role);
          localStorage.setItem('userId', data.user.id.toString());

          // Limpiar cualquier dato relacionado con el monitoreo
          localStorage.removeItem('dashboardData');
          localStorage.removeItem('monitoringActive');
        }

        // Handle redirects based on authentication
        const currentPath = router.pathname;
        const userRole = data.user.role;

        // Define routes
        const protectedRoutes = ['/dashboard'];
        const publicRoutes = ['/login', '/register'];
        const adminRoutes = ['/users'];

        // Handle redirects for authenticated users - avoid infinite redirects
        if (publicRoutes.includes(currentPath)) {
          setIsRedirecting(true);
          router.push('/dashboard');
        } else if (adminRoutes.includes(currentPath) && userRole !== 'admin') {
          setIsRedirecting(true);
          router.push('/dashboard');
        }
      } catch (error) {
        setIsAuthenticated(false);
        localStorage.removeItem('userRole');
        localStorage.removeItem('isAuthenticated');
        localStorage.removeItem('userId');
        localStorage.removeItem('dashboardData');
        localStorage.removeItem('monitoringActive');

        // Redirect to login if trying to access protected routes - avoid infinite redirects
        const currentPath = router.pathname;
        const protectedRoutes = ['/dashboard', '/users'];
        if (protectedRoutes.includes(currentPath)) {
          setIsRedirecting(true);
          router.push('/login');
        }
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, [router.pathname, isRedirecting]);

  // Reset redirecting state when route change completes
  useEffect(() => {
    setIsRedirecting(false);
  }, [router.pathname]);

  // Add global styles
  useEffect(() => {
    // Add global styles to body
    document.body.style.margin = '0';
    document.body.style.padding = '0';
    document.body.style.fontFamily =
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif';
  }, []);

  // Show loading state while verifying authentication
  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: '#1a1a1a',
        color: '#ffffff'
      }}>
        Loading...
      </div>
    );
  }

  return (
    <>
      <Head>
        <style>{`
          :root[data-theme='dark'] {
            color-scheme: dark;
          }

          html {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
          }

          body {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
          }
        `}</style>
      </Head>
      <Component {...pageProps} />
    </>
  );
}
