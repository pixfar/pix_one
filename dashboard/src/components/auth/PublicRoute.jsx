/**
 * Public Route Component
 *
 * Wraps routes that should redirect to dashboard if user is already authenticated
 * Used for sign-in and sign-up pages
 */

import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ROUTES } from '../../config/routes.constants';
import { Loader2 } from 'lucide-react';

const PublicRoute = ({ children }) => {
  const { isAuthenticated, isLoading, isValidating } = useAuth();

  // Show loading state while checking authentication
  if (isLoading || isValidating) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="text-center">
          <Loader2 className="w-12 h-12 mx-auto mb-4 text-primary animate-spin" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // Redirect to dashboard if already authenticated
  if (isAuthenticated) {
    return <Navigate to={ROUTES.DASHBOARD} replace />;
  }

  // Render children if not authenticated
  return children;
};

export default PublicRoute;
