/**
 * Index page component
 * Acts as a redirector to either login or dashboard based on authentication status
 */
import { useRouter } from 'next/router';
import { useEffect } from 'react';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // If authenticated, go to dashboard, otherwise go to login
    if (localStorage.getItem('isAuthenticated') === 'true') {
      router.push('/dashboard');
    } else {
      router.push('/login');
    }
  }, [router]);

  // Return null while redirecting
  return null;
}
