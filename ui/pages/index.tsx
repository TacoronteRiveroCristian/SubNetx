/**
 * Index page component
 * Acts as a redirector to either login or dashboard based on authentication status
 */
import { useEffect } from 'react';

export default function Home() {
  useEffect(() => {
    // If authenticated, go to dashboard, otherwise go to login
    if (localStorage.getItem('isAuthenticated') === 'true') {
      window.location.replace('/dashboard');
    } else {
      window.location.replace('/login');
    }
  }, []);

  // Return null while redirecting
  return null;
}
