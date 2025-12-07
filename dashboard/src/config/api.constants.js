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
  CREATE_SUBSCRIPTION: 'pix_one.api.subscriptions.create.create_subscription.create_subscription',
  GET_MY_SUBSCRIPTIONS: 'pix_one.api.subscriptions.list.get_subscriptions.get_my_subscriptions',
  GET_SUBSCRIPTION: 'pix_one.api.subscriptions.get.get_subscription.get_subscription',
  GET_SUBSCRIPTION_STATS: 'pix_one.api.subscriptions.list.get_subscriptions.get_subscription_stats',
  CANCEL_SUBSCRIPTION: 'pix_one.api.subscriptions.cancel.cancel_subscription.cancel_subscription',
  REACTIVATE_SUBSCRIPTION: 'pix_one.api.subscriptions.cancel.cancel_subscription.reactivate_subscription',
  INITIATE_PAYMENT: 'pix_one.api.subscriptions.create.create_subscription.initiate_subscription_payment',
};

// Payment Endpoints
export const PAYMENT_ENDPOINTS = {
  INITIATE: 'pix_one.api.payments.init_payment.init_payment_service.initiate_payment',
  INITIATE_SUBSCRIPTION: 'pix_one.api.payments.init_payment.init_subscription_payment.init_subscription_payment',
  SUCCESS: 'pix_one.api.payments.payment_success.payment_success_service.payment_success',
  CANCEL: 'pix_one.api.payments.payment_cancel.payment_cancel_service.payment_cancel',
  FAIL: 'pix_one.api.payments.payment_fail.payment_fail_service.payment_fail',
};

// Transaction Endpoints
export const TRANSACTION_ENDPOINTS = {
  GET_MY_TRANSACTIONS: 'pix_one.api.transactions.get_transactions.get_my_transactions',
  GET_TRANSACTION: 'pix_one.api.transactions.get_transactions.get_transaction',
  GET_TRANSACTION_STATS: 'pix_one.api.transactions.get_transactions.get_transaction_stats',
  GET_SUBSCRIPTION_TRANSACTIONS: 'pix_one.api.transactions.get_transactions.get_subscription_transactions',
};

// License Endpoints
export const LICENSE_ENDPOINTS = {
  VALIDATE: 'pix_one.api.license.validate_license',
  CHECK_STATUS: 'pix_one.api.license.check_license_status',
  UPDATE_USAGE: 'pix_one.api.license.update_license_usage',
  GET_DETAILS: 'pix_one.api.license.get_license_details',
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
  MY_SUBSCRIPTIONS: ['mySubscriptions'],
  SUBSCRIPTION_DETAILS: ['subscriptionDetails'],
  SUBSCRIPTION_STATS: ['subscriptionStats'],
  MY_TRANSACTIONS: ['myTransactions'],
  TRANSACTION_STATS: ['transactionStats'],
  BUSINESS: ['business'],
  PAYMENT_STATUS: ['paymentStatus'],
  LICENSE_DETAILS: ['licenseDetails'],
};
