/**
 * Subscription Service
 *
 * Handles all subscription and pricing-related API calls
 * Implements complete payment cycle with SSLCommerz
 */

import { SUBSCRIPTION_ENDPOINTS, PAYMENT_ENDPOINTS, TRANSACTION_ENDPOINTS } from '../config/api.constants';

/**
 * Get all subscription plans with pagination
 * @param {Function} call - Frappe call function
 * @param {Object} params - Query parameters
 * @returns {Promise} Subscription plans data
 */
export const getSubscriptionPlans = async (call, params = { page: 1, limit: 100 }) => {
  try {
    const response = await call(SUBSCRIPTION_ENDPOINTS.GET_PLANS, params);
    return response;
  } catch (error) {
    console.error('Get subscription plans error:', error);
    throw new Error(error.message || 'Failed to fetch subscription plans');
  }
};

/**
 * Create a new subscription (before payment)
 * @param {Function} call - Frappe call function
 * @param {Object} data - Subscription data
 * @param {string} data.plan_name - Plan name/ID
 * @param {string} data.app_name - App name (optional)
 * @returns {Promise} Subscription and payment data
 */
export const createSubscription = async (call, data) => {
  try {
    const response = await call(SUBSCRIPTION_ENDPOINTS.CREATE_SUBSCRIPTION, data);

    if (!response?.data) {
      throw new Error('Invalid response from server');
    }

    return response.data;
  } catch (error) {
    console.error('Create subscription error:', error);
    throw new Error(error.message || 'Failed to create subscription');
  }
};

/**
 * Initiate payment for subscription (simplified - only subscription ID needed)
 * @param {Function} call - Frappe call function
 * @param {string} subscriptionId - Subscription ID
 * @returns {Promise} Payment gateway URL and transaction ID
 */
export const initiateSubscriptionPayment = async (call, subscriptionId) => {
  try {
    const response = await call(PAYMENT_ENDPOINTS.INITIATE_SUBSCRIPTION, {
      subscription_id: subscriptionId,
    });

    if (!response?.data) {
      throw new Error('Invalid response from server');
    }

    return response.data;
  } catch (error) {
    console.error('Initiate subscription payment error:', error);
    throw new Error(error.message || 'Failed to initiate payment');
  }
};

/**
 * Get current user's subscriptions
 * @param {Function} call - Frappe call function
 * @param {Object} params - Query parameters
 * @returns {Promise} User subscriptions
 */
export const getMySubscriptions = async (call, params = { page: 1, limit: 10 }) => {
  try {
    const response = await call(SUBSCRIPTION_ENDPOINTS.GET_MY_SUBSCRIPTIONS, params);
    return response;
  } catch (error) {
    console.error('Get my subscriptions error:', error);
    throw new Error(error.message || 'Failed to fetch subscriptions');
  }
};

/**
 * Get subscription details by ID
 * @param {Function} call - Frappe call function
 * @param {string} subscriptionId - Subscription ID
 * @returns {Promise} Subscription details
 */
export const getSubscriptionDetails = async (call, subscriptionId) => {
  try {
    const response = await call(SUBSCRIPTION_ENDPOINTS.GET_SUBSCRIPTION, {
      subscription_id: subscriptionId,
    });
    return response;
  } catch (error) {
    console.error('Get subscription details error:', error);
    throw new Error(error.message || 'Failed to fetch subscription details');
  }
};

/**
 * Get subscription statistics
 * @param {Function} call - Frappe call function
 * @returns {Promise} Subscription statistics
 */
export const getSubscriptionStats = async (call) => {
  try {
    const response = await call(SUBSCRIPTION_ENDPOINTS.GET_SUBSCRIPTION_STATS);
    return response;
  } catch (error) {
    console.error('Get subscription stats error:', error);
    throw new Error(error.message || 'Failed to fetch subscription statistics');
  }
};

/**
 * Cancel a subscription
 * @param {Function} call - Frappe call function
 * @param {Object} data - Cancellation data
 * @param {string} data.subscription_id - Subscription ID
 * @param {string} data.reason - Cancellation reason
 * @param {string} data.notes - Additional notes
 * @param {boolean} data.immediate - Cancel immediately or at end of period
 * @returns {Promise} Cancelled subscription
 */
export const cancelSubscription = async (call, data) => {
  try {
    const response = await call(SUBSCRIPTION_ENDPOINTS.CANCEL_SUBSCRIPTION, data);
    return response;
  } catch (error) {
    console.error('Cancel subscription error:', error);
    throw new Error(error.message || 'Failed to cancel subscription');
  }
};

/**
 * Reactivate a cancelled subscription
 * @param {Function} call - Frappe call function
 * @param {string} subscriptionId - Subscription ID
 * @returns {Promise} Reactivated subscription
 */
export const reactivateSubscription = async (call, subscriptionId) => {
  try {
    const response = await call(SUBSCRIPTION_ENDPOINTS.REACTIVATE_SUBSCRIPTION, {
      subscription_id: subscriptionId,
    });
    return response;
  } catch (error) {
    console.error('Reactivate subscription error:', error);
    throw new Error(error.message || 'Failed to reactivate subscription');
  }
};

/**
 * Get user's payment transactions
 * @param {Function} call - Frappe call function
 * @param {Object} params - Query parameters
 * @returns {Promise} Transaction list
 */
export const getMyTransactions = async (call, params = { page: 1, limit: 10 }) => {
  try {
    const response = await call(TRANSACTION_ENDPOINTS.GET_MY_TRANSACTIONS, params);
    return response;
  } catch (error) {
    console.error('Get my transactions error:', error);
    throw new Error(error.message || 'Failed to fetch transactions');
  }
};

/**
 * Get transaction statistics
 * @param {Function} call - Frappe call function
 * @param {string} subscriptionId - Optional subscription ID to filter
 * @returns {Promise} Transaction statistics
 */
export const getTransactionStats = async (call, subscriptionId = null) => {
  try {
    const params = subscriptionId ? { subscription_id: subscriptionId } : {};
    const response = await call(TRANSACTION_ENDPOINTS.GET_TRANSACTION_STATS, params);
    return response;
  } catch (error) {
    console.error('Get transaction stats error:', error);
    throw new Error(error.message || 'Failed to fetch transaction statistics');
  }
};

/**
 * Get transactions for a specific subscription
 * @param {Function} call - Frappe call function
 * @param {string} subscriptionId - Subscription ID
 * @param {Object} params - Query parameters
 * @returns {Promise} Subscription transactions
 */
export const getSubscriptionTransactions = async (call, subscriptionId, params = { page: 1, limit: 10 }) => {
  try {
    const response = await call(TRANSACTION_ENDPOINTS.GET_SUBSCRIPTION_TRANSACTIONS, {
      subscription_id: subscriptionId,
      ...params,
    });
    return response;
  } catch (error) {
    console.error('Get subscription transactions error:', error);
    throw new Error(error.message || 'Failed to fetch subscription transactions');
  }
};

/**
 * Complete purchase flow - Create subscription and initiate payment
 * User must be logged in. Customer info fetched from session automatically.
 * @param {Function} call - Frappe call function
 * @param {Object} planData - Selected plan data
 * @param {string} planData.plan_name - Plan name/ID
 * @param {string} planData.app_name - App name (optional)
 * @returns {Promise} Payment gateway URL to redirect user
 */
export const purchasePlan = async (call, planData) => {
  try {
    // Step 1: Create subscription (customer info fetched from session on backend)
    const subscriptionResponse = await createSubscription(call, {
      plan_name: planData.plan_name,
      app_name: planData.app_name || 'Pix One',
    });

    if (!subscriptionResponse?.subscription) {
      throw new Error('Invalid subscription response');
    }

    const subscription = subscriptionResponse.subscription;

    // Step 2: Initiate payment with only subscription ID
    // Backend will fetch customer info from session and subscription details
    const paymentResponse = await initiateSubscriptionPayment(call, subscription.name);

    if (!paymentResponse?.gateway_url) {
      throw new Error('Payment gateway URL not received');
    }

    return {
      subscription,
      paymentUrl: paymentResponse.gateway_url,
      transactionId: paymentResponse.transaction_id,
    };
  } catch (error) {
    console.error('Purchase plan error:', error);
    throw new Error(error.message || 'Failed to complete purchase');
  }
};

/**
 * Renew subscription with payment
 * Simplified - only subscription ID needed, customer info fetched from session
 * @param {Function} call - Frappe call function
 * @param {string} subscriptionId - Subscription ID to renew
 * @returns {Promise} Payment gateway URL
 */
export const renewSubscription = async (call, subscriptionId) => {
  try {
    // Initiate payment with only subscription ID
    // Backend fetches customer info from session and subscription details
    const paymentResponse = await initiateSubscriptionPayment(call, subscriptionId);

    if (!paymentResponse?.gateway_url) {
      throw new Error('Payment gateway URL not received');
    }

    return {
      paymentUrl: paymentResponse.gateway_url,
      transactionId: paymentResponse.transaction_id,
    };
  } catch (error) {
    console.error('Renew subscription error:', error);
    throw new Error(error.message || 'Failed to renew subscription');
  }
};

/**
 * Utility: Format currency for display
 * @param {number} amount - Amount to format
 * @param {string} currency - Currency code (default: BDT)
 * @returns {string} Formatted currency string
 */
export const formatCurrency = (amount, currency = 'BDT') => {
  return new Intl.NumberFormat('en-BD', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
};

/**
 * Utility: Calculate subscription end date
 * @param {string} startDate - Start date
 * @param {string} billingInterval - Billing interval (Monthly, Quarterly, Yearly)
 * @returns {Date} End date
 */
export const calculateEndDate = (startDate, billingInterval) => {
  const start = new Date(startDate);
  let months = 1;

  switch (billingInterval) {
    case 'Monthly':
      months = 1;
      break;
    case 'Quarterly':
      months = 3;
      break;
    case 'Yearly':
      months = 12;
      break;
    case 'Lifetime':
      return new Date(start.getFullYear() + 100, start.getMonth(), start.getDate());
    default:
      months = 1;
  }

  return new Date(start.getFullYear(), start.getMonth() + months, start.getDate());
};

/**
 * Utility: Get subscription status badge color
 * @param {string} status - Subscription status
 * @returns {string} Tailwind color class
 */
export const getStatusColor = (status) => {
  const statusColors = {
    Active: 'bg-green-100 text-green-800 border-green-200',
    Trial: 'bg-blue-100 text-blue-800 border-blue-200',
    'Pending Payment': 'bg-yellow-100 text-yellow-800 border-yellow-200',
    'Past Due': 'bg-orange-100 text-orange-800 border-orange-200',
    Expired: 'bg-gray-100 text-gray-800 border-gray-200',
    Cancelled: 'bg-red-100 text-red-800 border-red-200',
    Suspended: 'bg-purple-100 text-purple-800 border-purple-200',
  };

  return statusColors[status] || 'bg-gray-100 text-gray-800 border-gray-200';
};

/**
 * Utility: Get transaction status color
 * @param {string} status - Transaction status
 * @returns {string} Tailwind color class
 */
export const getTransactionStatusColor = (status) => {
  const statusColors = {
    Completed: 'bg-green-100 text-green-800',
    Pending: 'bg-yellow-100 text-yellow-800',
    Initiated: 'bg-blue-100 text-blue-800',
    Processing: 'bg-blue-100 text-blue-800',
    Failed: 'bg-red-100 text-red-800',
    Cancelled: 'bg-gray-100 text-gray-800',
    Refunded: 'bg-purple-100 text-purple-800',
    'Partially Refunded': 'bg-purple-100 text-purple-800',
  };

  return statusColors[status] || 'bg-gray-100 text-gray-800';
};
