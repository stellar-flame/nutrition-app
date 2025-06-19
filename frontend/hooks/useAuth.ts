import { useState, useEffect } from 'react';
import { User, onAuthStateChanged, signOut } from 'firebase/auth';
import { auth } from '../firebase/firebaseConfig';
import api from '../api/axios';

// Define the return type for our custom hook
interface UseAuthReturn {
  user: User | null;
  isLoading: boolean;
  login: (idToken: string) => Promise<void>;
  logout: () => Promise<void>;
  error: string | null;
}

/**
 * Custom hook for managing Firebase authentication
 * 
 * LEARNING CONCEPTS:
 * 1. Custom Hooks - Extract stateful logic into reusable functions
 * 2. TypeScript interfaces - Define exact return types
 * 3. useEffect cleanup - Prevent memory leaks with unsubscribe
 * 4. Error handling - Centralized auth error management
 * 5. Async operations - Handle promises in hooks
 */
export const useAuth = (): UseAuthReturn => {
  // State management - same useState pattern you know
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Effect for Firebase auth listener
  useEffect(() => {
    console.log('🔧 Setting up Firebase auth listener...');
    
    // onAuthStateChanged returns an unsubscribe function
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      console.log('👤 Auth state changed:', currentUser ? 'Logged in' : 'Logged out');
      setUser(currentUser);
      setIsLoading(false); // Auth state is now determined
      setError(null); // Clear any previous errors
    });

    // CRITICAL: Return cleanup function to prevent memory leaks
    // This runs when component unmounts or effect re-runs
    return () => {
      console.log('🧹 Cleaning up Firebase auth listener');
      unsubscribe();
    };
  }, []); // Empty dependency array = run once on mount

  // Login function - async operation with error handling
  const login = async (idToken: string): Promise<void> => {
    try {
      setError(null);
      console.log('🔐 Verifying token with backend...');
      
      // Send token to your backend for verification
      const { data } = await api.get('/auth/verify', {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      
      console.log('✅ User verified:', data);
      // Note: Firebase auth will automatically update user state
      // through the onAuthStateChanged listener above
      
    } catch (error) {
      const errorMessage = 'Token verification failed';
      console.error('❌ Login error:', error);
      setError(errorMessage);
      throw new Error(errorMessage); // Re-throw so UI can handle it
    }
  };

  // Logout function - simple but with error handling
  const logout = async (): Promise<void> => {
    try {
      setError(null);
      console.log('🚪 Signing out...');
      await signOut(auth);
      console.log('✅ Signed out successfully');
    } catch (error) {
      const errorMessage = 'Logout failed';
      console.error('❌ Logout error:', error);
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  // Return object with all auth state and functions
  return {
    user,
    isLoading,
    login,
    logout,
    error,
  };
};
