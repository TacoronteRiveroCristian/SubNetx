/**
 * Root page component that redirects to login by default
 * Acts as the entry point for the application
 */
import { useRouter } from 'next/router'; // Import useRouter for navigation
import { useEffect } from 'react'; // Import useEffect for side effects

// Define the Index component that will redirect to login
export default function Index() {
  // Initialize router for redirection
  const router = useRouter();

  // Effect that runs on component mount
  useEffect(() => {
    // Check if user is authenticated
    const isAuthenticated = typeof window !== 'undefined' && localStorage.getItem('isAuthenticated') === 'true';

    // Redirect to login if not authenticated, otherwise to dashboard
    if (!isAuthenticated) {
      router.push('/login');
    } else {
      router.push('/dashboard');
    }
  }, [router]);

  // Return empty div while redirecting
  return <div style={{ display: 'none' }} />;
}
