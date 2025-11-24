/**
 * Route Configuration
 *
 * Centralized route paths for the application
 */

export const ROUTES = {
  HOME: '/',
  PRICING: '/pricing',
  SIGN_IN: '/signin',
  SIGN_UP: '/signup',
  DASHBOARD: '/dashboard',
  PROFILE: '/dashboard/profile',
  SETTINGS: '/dashboard/settings',
  CUSTOMERS: '/dashboard/customers',
  PRODUCTS: '/dashboard/products',
};

// Public routes that don't require authentication
export const PUBLIC_ROUTES = [
  ROUTES.HOME,
  ROUTES.PRICING,
  ROUTES.SIGN_IN,
  ROUTES.SIGN_UP,
];

// Protected routes that require authentication
export const PROTECTED_ROUTES = [
  ROUTES.DASHBOARD,
  ROUTES.PROFILE,
  ROUTES.SETTINGS,
  ROUTES.CUSTOMERS,
  ROUTES.PRODUCTS,
];
