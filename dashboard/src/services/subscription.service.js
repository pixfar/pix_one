/**
 * Subscription Service
 *
 * Handles subscription and pricing-related API calls
 */

import { SUBSCRIPTION_ENDPOINTS, API_CONFIG } from '../config/api.constants';

/**
 * Get all subscription plans
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number
 * @param {number} params.limit - Items per page
 * @param {string} params.sort - Sort field
 * @param {string} params.order - Sort order (asc/desc)
 * @returns {Promise} Subscription plans data
 */
export const getSubscriptionPlans = async (
  params = {
    page: API_CONFIG.DEFAULT_PAGE,
    limit: API_CONFIG.DEFAULT_LIMIT,
    sort: 'view_order',
    order: 'asc',
  }
) => {
  return {
    endpoint: SUBSCRIPTION_ENDPOINTS.GET_PLANS,
    params,
  };
};

/**
 * Get plan details by ID
 * @param {string} planId - Plan ID
 * @returns {Promise} Plan details
 */
export const getPlanDetails = async (planId) => {
  return {
    endpoint: SUBSCRIPTION_ENDPOINTS.GET_PLAN_DETAILS,
    params: { plan_id: planId },
  };
};

/**
 * Subscribe to a plan
 * @param {Object} subscriptionData - Subscription data
 * @param {string} subscriptionData.plan_id - Plan ID
 * @param {Function} call - Frappe call function
 * @returns {Promise} Subscription response
 */
export const subscribeToPlan = async (subscriptionData, call) => {
  try {
    const response = await call(SUBSCRIPTION_ENDPOINTS.SUBSCRIBE, subscriptionData);
    return response;
  } catch (error) {
    throw new Error(error.message || 'Subscription failed');
  }
};
