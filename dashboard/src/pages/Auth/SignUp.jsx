/**
 * Sign Up Page
 *
 * Two-column layout with registration form and welcome message
 * Simplified design with theme colors
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useFrappePostCall } from 'frappe-react-sdk';
import { AUTH_ENDPOINTS } from '../../config/api.constants';
import { ROUTES } from '../../config/routes.constants';
import { Loader2, CheckCircle } from 'lucide-react';
import Navbar from '../../components/Shared/Navbar';
import Footer from '../../components/Shared/Footer';

const SignUp = () => {
  const navigate = useNavigate();
  const { call, loading: isSubmitting } = useFrappePostCall(AUTH_ENDPOINTS.SIGN_UP);

  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
  });

  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    // Clear error when user starts typing
    if (error) setError('');
  };

  const validateForm = () => {
    if (!formData.fullName || !formData.email) {
      setError('All fields are required');
      return false;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!validateForm()) {
      return;
    }

    try {
      const response = await call({
        email: formData.email,
        full_name: formData.fullName,
        redirect_to: window.location.origin + '/pixone' + ROUTES.SIGN_IN,
      });

      if (response) {
        setSuccess(true);
        // Redirect to sign-in after 3 seconds
        setTimeout(() => {
          navigate(ROUTES.SIGN_IN);
        }, 3000);
      }
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
    }
  };

  // Success screen
  if (success) {
    return (
      <div className="min-h-screen flex flex-col bg-background">
        <Navbar />
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="w-full max-w-md bg-card rounded-xl shadow-2xl p-8 text-center border border-border">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-foreground mb-2">
              Thank you for registering!
            </h1>
            <p className="text-muted-foreground mb-6">
              Please check your inbox and click the verification link to activate your account.
            </p>
            <p className="text-sm text-muted-foreground">Redirecting to sign in page...</p>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <Navbar />

      {/* Main Content - Two Column Layout */}
      <div className="flex-1 flex my-8 max-w-[1280px] mx-auto w-full">
        {/* Left Column - Sign Up Form */}
        <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-card rounded-l-2xl">
          <div className="w-full max-w-md">
            {/* Logo */}
            <div className="mb-12">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center">
                  <div className="w-6 h-6 bg-primary-foreground rounded-sm"></div>
                </div>
                <span className="text-xl font-semibold text-foreground">PixOne</span>
              </div>
            </div>

            {/* Create Account */}
            <div className="mb-8">
              <h1 className="text-4xl font-bold text-foreground mb-3">Create Account</h1>
              <p className="text-muted-foreground text-lg">Start your journey with PixOne today</p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}

            {/* Sign Up Form */}
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Full Name Field */}
              <div>
                <label htmlFor="fullName" className="block text-sm font-medium text-foreground mb-2">
                  Full Name<span className="text-destructive">*</span>
                </label>
                <input
                  type="text"
                  id="fullName"
                  name="fullName"
                  value={formData.fullName}
                  onChange={handleChange}
                  placeholder="Enter your full name"
                  className="w-full px-4 py-3 bg-background border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all text-foreground placeholder:text-muted-foreground"
                  disabled={isSubmitting}
                />
              </div>

              {/* Email Field */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-foreground mb-2">
                  Email address<span className="text-destructive">*</span>
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="Enter your email address"
                  className="w-full px-4 py-3 bg-background border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all text-foreground placeholder:text-muted-foreground"
                  disabled={isSubmitting}
                />
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-primary text-primary-foreground py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-8"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  'Create Account'
                )}
              </button>
            </form>

            {/* Sign In Link */}
            <p className="mt-8 text-center text-sm text-muted-foreground">
              Already have an account?{' '}
              <Link to={ROUTES.SIGN_IN} className="text-primary font-medium hover:underline">
                Sign in
              </Link>
            </p>
          </div>
        </div>

        {/* Right Column - Welcome Message with Decorative Design */}
        <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary/5 via-background to-accent/5 relative overflow-hidden border-l border-border rounded-r-2xl">
          {/* Decorative Elements - Top */}
          <div className="absolute top-10 right-10 w-32 h-32 bg-primary/10 rounded-full blur-3xl"></div>
          <div className="absolute top-20 right-32 w-24 h-24 bg-accent/10 rounded-full blur-2xl"></div>

          {/* Decorative Elements - Bottom */}
          <div className="absolute bottom-10 left-10 w-40 h-40 bg-primary/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 left-32 w-32 h-32 bg-accent/10 rounded-full blur-2xl"></div>

          {/* Center Content */}
          <div className="flex flex-col items-center justify-center w-full p-12 relative z-10">
            {/* Large Decorative "JK" letters as per screenshot */}
            <div className="mb-8 opacity-5 absolute inset-0 flex items-center justify-center">
              <div className="text-[20rem] font-bold text-foreground/5 leading-none">JK</div>
            </div>

            {/* Main Card */}
            <div className="bg-card/50 backdrop-blur-lg border border-border rounded-2xl p-8 max-w-md relative shadow-lg">
              {/* Logo Icon */}
              <div className="absolute -top-6 right-8 w-12 h-12 bg-primary rounded-xl flex items-center justify-center shadow-lg">
                <div className="w-6 h-6 bg-primary-foreground rounded-sm"></div>
              </div>

              <h2 className="text-3xl font-bold text-foreground mb-4">
                Welcome! Create your PixOne account
              </h2>
              <p className="text-muted-foreground text-base">
                Join thousands of businesses using PixOne to manage their operations efficiently.
                Get started with our all-in-one business management platform.
              </p>
            </div>

            {/* Bottom Card */}
            <div className="mt-8 bg-card/50 backdrop-blur-lg border border-border rounded-2xl p-6 max-w-md shadow-lg">
              <h3 className="text-xl font-bold text-foreground mb-3">Get started in minutes</h3>
              <p className="text-muted-foreground text-sm mb-4">
                Quick setup with instant access to all features. Start managing your business smarter, not harder.
              </p>

              {/* Avatar Group */}
              <div className="flex items-center gap-2">
                <div className="flex -space-x-2">
                  <div className="w-8 h-8 rounded-full bg-primary/20 border-2 border-border flex items-center justify-center">
                    <span className="text-xs text-foreground font-medium">U1</span>
                  </div>
                  <div className="w-8 h-8 rounded-full bg-primary/20 border-2 border-border flex items-center justify-center">
                    <span className="text-xs text-foreground font-medium">U2</span>
                  </div>
                  <div className="w-8 h-8 rounded-full bg-primary/20 border-2 border-border flex items-center justify-center">
                    <span className="text-xs text-foreground font-medium">U3</span>
                  </div>
                </div>
                <span className="text-sm text-muted-foreground">+3695 users joined</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <Footer />
    </div>
  );
};

export default SignUp;
