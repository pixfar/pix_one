/**
 * API Endpoints Configuration
 *
 * This file contains all API endpoint constants used throughout the application.
 * Using Frappe React SDK, we only need the method path without base URL.
 */

// Authentication Endpoints
export const AUTH_ENDPOINTS = {
  SIGN_UP: 'frappe.core.doctype.user.user.sign_up',
  LOGIN: 'login',
  LOGOUT: 'logout',
  GET_CURRENT_USER: 'frappe.auth.get_logged_user',
  RESET_PASSWORD: 'frappe.core.doctype.user.user.reset_password',
  UPDATE_PASSWORD: 'frappe.core.doctype.user.user.update_password',
};

// Subscription & Pricing Endpoints
export const SUBSCRIPTION_ENDPOINTS = {
  GET_PLANS: 'pix_one.api.subscription_plans.get_plans.get_plans.get_subscription_plans',
  GET_PLAN_DETAILS: 'pix_one.api.subscription_plans.get_plan_details',
  SUBSCRIBE: 'pix_one.api.subscription_plans.subscribe',
};

// Payment Endpoints
export const PAYMENT_ENDPOINTS = {
  INITIATE: 'pix_one.api.payments.init_payment.initiate_payment',
  SUCCESS: 'pix_one.api.payments.payment_success.handle_success',
  CANCEL: 'pix_one.api.payments.payment_cancel.handle_cancel',
  FAIL: 'pix_one.api.payments.payment_fail.handle_fail',
};

// Business/User Management Endpoints
export const BUSINESS_ENDPOINTS = {
  GET_BUSINESS: 'pix_one.api.business.get_business',
  CREATE_BUSINESS: 'pix_one.api.business.create_business',
  UPDATE_BUSINESS: 'pix_one.api.business.update_business',
};

// Default API Configuration
export const API_CONFIG = {
  DEFAULT_PAGE: 1,
  DEFAULT_LIMIT: 10,
  MAX_LIMIT: 100,
  CACHE_TIME: 5 * 60 * 1000, // 5 minutes
  STALE_TIME: 2 * 60 * 1000, // 2 minutes
};

// Query Keys for React Query
export const QUERY_KEYS = {
  CURRENT_USER: ['currentUser'],
  SUBSCRIPTION_PLANS: ['subscriptionPlans'],
  BUSINESS: ['business'],
  PAYMENT_STATUS: ['paymentStatus'],
};
