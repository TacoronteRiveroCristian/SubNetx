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
  // In a real app, this would check a token or session
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Effect to run on component mount and route changes
  useEffect(() => {
    // Check if user is authenticated via localStorage
    const isUserAuthenticated = localStorage.getItem('isAuthenticated') === 'true';

    // Update authentication state
    setIsAuthenticated(isUserAuthenticated);

    // If user is not authenticated and not on login page, redirect to login
    if (!isUserAuthenticated && router.pathname !== '/login') {
      router.push('/login');
    }
  }, [router.pathname]);

  // Add global styles
  useEffect(() => {
    // Add global styles to body
    document.body.style.margin = '0';
    document.body.style.padding = '0';
    document.body.style.fontFamily =
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif';
  }, []);

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
