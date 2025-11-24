/**
 * Authentication Service
 *
 * Handles all authentication-related API calls using Frappe React SDK
 */

import { AUTH_ENDPOINTS } from '../config/api.constants';

/**
 * Sign up a new user
 * @param {Object} userData - User registration data
 * @param {string} userData.email - User email
 * @param {string} userData.full_name - User full name
 * @param {string} userData.redirect_to - Redirect URL after signup
 * @returns {Promise} API response
 */
export const signUpUser = async (userData, call) => {
  try {
    const response = await call(AUTH_ENDPOINTS.SIGN_UP, {
      email: userData.email,
      full_name: userData.full_name,
      redirect_to: userData.redirect_to || window.location.origin,
    });
    return response;
  } catch (error) {
    throw new Error(error.message || 'Sign up failed');
  }
};

/**
 * Login user
 * @param {Object} credentials - Login credentials
 * @param {string} credentials.username - Username or email
 * @param {string} credentials.password - Password
 * @param {Function} loginFn - Frappe auth login function
 * @returns {Promise} Login response
 */
export const loginUser = async (credentials, loginFn) => {
  try {
    const response = await loginFn({
      username: credentials.username.trim(),
      password: credentials.password.trim(),
    });
    return response;
  } catch (error) {
    throw new Error(error.message || 'Login failed');
  }
};

/**
 * Logout user
 * @param {Function} logoutFn - Frappe auth logout function
 * @returns {Promise} Logout response
 */
export const logoutUser = async (logoutFn) => {
  try {
    await logoutFn();
  } catch (error) {
    throw new Error(error.message || 'Logout failed');
  }
};

/**
 * Get current logged-in user
 * @param {Function} call - Frappe call function
 * @returns {Promise} User data
 */
export const getCurrentUser = async (call) => {
  try {
    const response = await call(AUTH_ENDPOINTS.GET_CURRENT_USER);
    return response;
  } catch (error) {
    throw new Error(error.message || 'Failed to fetch user data');
  }
};

/**
 * Reset password request
 * @param {string} email - User email
 * @param {Function} call - Frappe call function
 * @returns {Promise} API response
 */
export const resetPassword = async (email, call) => {
  try {
    const response = await call(AUTH_ENDPOINTS.RESET_PASSWORD, {
      user: email,
    });
    return response;
  } catch (error) {
    throw new Error(error.message || 'Password reset failed');
  }
};

/**
 * Update user password
 * @param {Object} passwordData - Password data
 * @param {string} passwordData.old_password - Current password
 * @param {string} passwordData.new_password - New password
 * @param {Function} call - Frappe call function
 * @returns {Promise} API response
 */
export const updatePassword = async (passwordData, call) => {
  try {
    const response = await call(AUTH_ENDPOINTS.UPDATE_PASSWORD, {
      old_password: passwordData.old_password,
      new_password: passwordData.new_password,
    });
    return response;
  } catch (error) {
    throw new Error(error.message || 'Password update failed');
  }
};
