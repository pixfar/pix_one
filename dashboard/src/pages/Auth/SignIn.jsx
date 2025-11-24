/**
 * Sign In Page
 *
 * Two-column layout with login form and welcome message
 * Simplified design with theme colors
 */

import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ROUTES } from '../../config/routes.constants';
import { Eye, EyeOff, Loader2 } from 'lucide-react';
import Navbar from '../../components/Shared/Navbar';
import Footer from '../../components/Shared/Footer';

const SignIn = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isLoading } = useAuth();

  const [formData, setFormData] = useState({
    username: '',
    password: '',
    rememberMe: false,
  });

  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Get the redirect path from location state or default to dashboard
  const from = location.state?.from?.pathname || ROUTES.DASHBOARD;

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    // Clear error when user starts typing
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!formData.username || !formData.password) {
      setError('Please enter both email and password');
      return;
    }

    setIsSubmitting(true);

    try {
      const result = await login({
        username: formData.username,
        password: formData.password,
      });

      if (result.success) {
        // Redirect to the page they tried to visit or dashboard
        navigate(from, { replace: true });
      } else {
        setError(result.error || 'Invalid email or password');
      }
    } catch (err) {
      setError(err.message || 'An error occurred. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <Navbar />

      {/* Main Content - Two Column Layout */}
      <div className="flex-1 flex my-8 max-w-[1280px] mx-auto w-full">
        {/* Left Column - Login Form */}
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

            {/* Welcome Back */}
            <div className="mb-8">
              <h1 className="text-4xl font-bold text-foreground mb-3">Welcome Back</h1>
              <p className="text-muted-foreground text-lg">Sign in to your PixOne account to continue</p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}

            {/* Login Form */}
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Email Field */}
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-foreground mb-2">
                  Email address<span className="text-destructive">*</span>
                </label>
                <input
                  type="text"
                  id="username"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  placeholder="Enter your email address"
                  className="w-full px-4 py-3 bg-background border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all text-foreground placeholder:text-muted-foreground"
                  disabled={isSubmitting}
                />
              </div>

              {/* Password Field */}
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-foreground mb-2">
                  Password<span className="text-destructive">*</span>
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="••••••••••••••"
                    className="w-full px-4 py-3 bg-background border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all text-foreground placeholder:text-muted-foreground pr-12"
                    disabled={isSubmitting}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              {/* Remember Me & Forgot Password */}
              <div className="flex items-center justify-between">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    name="rememberMe"
                    checked={formData.rememberMe}
                    onChange={handleChange}
                    className="w-4 h-4 text-primary border-input rounded focus:ring-ring focus:ring-2"
                    disabled={isSubmitting}
                  />
                  <span className="ml-2 text-sm text-foreground">Remember Me</span>
                </label>
                <Link to="/forgot-password" className="text-sm text-primary hover:underline">
                  Forgot Password?
                </Link>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isSubmitting || isLoading}
                className="w-full bg-primary text-primary-foreground py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-8"
              >
                {isSubmitting || isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  'Sign In to PixOne'
                )}
              </button>
            </form>

            {/* Sign Up Link */}
            <p className="mt-8 text-center text-sm text-muted-foreground">
              New on our platform?{' '}
              <Link to={ROUTES.SIGN_UP} className="text-primary font-medium hover:underline">
                Create an account
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
                Welcome back! Please sign in to your PixOne account
              </h2>
              <p className="text-muted-foreground text-base">
                Access your comprehensive business management platform. Manage your operations,
                finances, and team all in one place.
              </p>
            </div>

            {/* Bottom Card */}
            <div className="mt-8 bg-card/50 backdrop-blur-lg border border-border rounded-2xl p-6 max-w-md shadow-lg">
              <h3 className="text-xl font-bold text-foreground mb-3">Trusted by businesses worldwide</h3>
              <p className="text-muted-foreground text-sm mb-4">
                Join thousands of companies using PixOne to streamline their operations and grow their business.
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
                <span className="text-sm text-muted-foreground">+3695</span>
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

export default SignIn;
