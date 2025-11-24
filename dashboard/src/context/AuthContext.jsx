/**
 * Authentication Context
 *
 * Provides authentication state and methods throughout the application
 * Wraps Frappe React SDK's useFrappeAuth hook with additional functionality
 */

import { createContext, useContext, useEffect, useState } from 'react';
import { useFrappeAuth } from 'frappe-react-sdk';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const {
    currentUser,
    isValidating,
    isLoading,
    login,
    logout,
    error: authError,
    updateCurrentUser,
    getUserCookie,
  } = useFrappeAuth();

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);

  // Check if user is authenticated
  useEffect(() => {
    if (currentUser && !currentUser.includes('Guest')) {
      setIsAuthenticated(true);
      setUser(currentUser);
    } else {
      setIsAuthenticated(false);
      setUser(null);
    }
  }, [currentUser]);

  // Handle login
  const handleLogin = async (credentials) => {
    try {
      await login({
        username: credentials.username.trim(),
        password: credentials.password.trim(),
      });
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Login failed. Please check your credentials.',
      };
    }
  };

  // Handle logout
  const handleLogout = async () => {
    try {
      await logout();
      setIsAuthenticated(false);
      setUser(null);
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Logout failed.',
      };
    }
  };

  const value = {
    // State
    isAuthenticated,
    user,
    currentUser,
    isValidating,
    isLoading,
    authError,

    // Methods
    login: handleLogin,
    logout: handleLogout,
    updateCurrentUser,
    getUserCookie,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
