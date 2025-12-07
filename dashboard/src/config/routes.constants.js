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

  // Payment routes
  PAYMENT_SUCCESS: '/payment/success',
  PAYMENT_FAILED: '/payment/failed',
  PAYMENT_CANCELLED: '/payment/cancelled',

  // Subscription routes
  SUBSCRIPTIONS: '/dashboard/subscriptions',
  SUBSCRIPTION_DETAILS: '/dashboard/subscriptions/:id',

  // Transaction routes
  TRANSACTIONS: '/dashboard/transactions',
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
  ROUTES.PAYMENT_SUCCESS,
  ROUTES.PAYMENT_FAILED,
  ROUTES.PAYMENT_CANCELLED,
  ROUTES.SUBSCRIPTIONS,
  ROUTES.SUBSCRIPTION_DETAILS,
  ROUTES.TRANSACTIONS,
];
