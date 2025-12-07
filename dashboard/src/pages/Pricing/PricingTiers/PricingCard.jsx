import React, { useState } from 'react';
import { Check, Star, Loader2 } from 'lucide-react';
import { useFrappePostCall, useFrappeGetCall } from 'frappe-react-sdk';
import { toast } from 'sonner';
import { SUBSCRIPTION_ENDPOINTS, PAYMENT_ENDPOINTS, AUTH_ENDPOINTS } from '@/config/api.constants';

const PricingCard = ({ plan, isPopular = false }) => {
  const [loading, setLoading] = useState(false);

  // Use useFrappePostCall for making API calls
  const { call: createSubscription } = useFrappePostCall(SUBSCRIPTION_ENDPOINTS.CREATE_SUBSCRIPTION);
  const { call: initiatePayment } = useFrappePostCall(PAYMENT_ENDPOINTS.INITIATE);

  // Get current user info
  const { data: currentUser } = useFrappeGetCall('frappe.auth.get_logged_user');
  // Use features from API if available, otherwise use default list
  const features = plan.features && plan.features.length > 0
    ? plan.features.map(f => ({
        name: f.feature_name,
        isKey: f.is_key_feature === 1
      }))
    : [
        { name: 'All apps', isKey: false },
        { name: 'Unlimited users', isKey: false },
        { name: 'Unlimited support', isKey: false },
        { name: 'Hosting and maintenance', isKey: false }
      ];

  const handlePurchase = async () => {
    try {
      setLoading(true);

      // Check if user is logged in
      if (!currentUser) {
        toast.error('Please login to purchase a subscription');
        setLoading(false);
        return;
      }

      // Step 1: Create subscription
      const subscriptionResponse = await createSubscription({
        plan_name: plan.plan_name
      });

      if (!subscriptionResponse?.data?.subscription) {
        throw new Error('Failed to create subscription');
      }

      const subscription = subscriptionResponse.data.subscription;

      // Step 2: Get user details for payment
      const userResponse = await fetch('/api/method/frappe.client.get', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          doctype: 'User',
          name: currentUser
        })
      });

      const userData = await userResponse.json();
      const user = userData.message;

      // Calculate total amount (price + setup_fee)
      const totalAmount = (plan.price || 0) + (plan.setup_fee || 0);

      // Step 3: Initiate payment with all required data
      console.log('Initiating payment with data:', {
        total_amount: totalAmount,
        currency: plan.currency || 'BDT',
        product_name: `${plan.plan_name} Subscription`,
        subscription_id: subscription.name,
        cus_name: user.full_name || user.name,
        cus_email: user.email
      });

      const paymentResponse = await initiatePayment({
        total_amount: totalAmount,
        currency: plan.currency || 'BDT',
        product_name: `${plan.plan_name} Subscription`,
        product_category: 'Subscription',
        cus_name: user.full_name || user.name,
        cus_email: user.email,
        cus_phone: user.phone || user.mobile_no || '01700000000',
        cus_add1: user.location || 'N/A',
        cus_city: 'Dhaka',
        cus_country: 'Bangladesh',
        num_of_item: 1,
        shipping_method: 'NO',
        // Subscription reference data
        subscription_id: subscription.name,
        plan_name: plan.plan_name,
        transaction_type: 'Initial Payment'
      });

      console.log('Payment response:', paymentResponse);

      // Check for gateway URL in different response formats
      const gatewayUrl = paymentResponse?.message?.gateway_url ||
                        paymentResponse?.data?.gateway_url ||
                        paymentResponse?.gateway_url;

      if (!gatewayUrl) {
        console.error('Payment response missing gateway_url:', paymentResponse);
        throw new Error('Payment gateway URL not received');
      }

      console.log('Redirecting to:', gatewayUrl);
      // Redirect to SSLCommerz payment gateway
      window.location.href = gatewayUrl;

    } catch (error) {
      console.error('Purchase failed:', error);
      toast.error(error.message || 'Failed to initiate purchase. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div
      className={`relative flex flex-col bg-card border rounded-2xl p-8 transition-all duration-300 hover:shadow-2xl ${
        isPopular
          ? 'border-primary shadow-xl shadow-primary/20 scale-105'
          : 'border-border hover:border-primary/40'
      }`}
    >
      {/* Popular Badge */}
      {isPopular && (
        <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
          <span className="px-4 py-2 bg-primary text-primary-foreground text-sm font-semibold rounded-full shadow-lg">
            Most Popular
          </span>
        </div>
      )}

      {/* Plan Name */}
      <h3 className="text-2xl font-bold text-foreground mb-2">{plan.plan_name}</h3>

      {/* Price */}
      <div className="mb-6">
        <div className="flex items-baseline gap-2">
          <span className="text-5xl font-bold text-foreground">$</span>
          <span className="text-6xl font-bold text-foreground">
            {Math.floor(plan.price)}
          </span>
          <span className="text-2xl font-bold text-foreground">
            .{((plan.price % 1) * 100).toFixed(0).padStart(2, '0')}
          </span>
        </div>
        <p className="text-muted-foreground mt-2">/ user / month</p>
      </div>

      {/* Short Description */}
      <div className="mb-8">
        {plan.short_description?.split('\n').map((line, idx) => (
          <p key={idx} className="text-muted-foreground text-sm leading-relaxed">
            {line}
          </p>
        ))}
      </div>

      {/* Features List */}
      <div className="flex-1 mb-8">
        <ul className="space-y-4">
          {features.map((feature, idx) => (
            <li key={idx} className="flex items-start gap-3">
              {feature.isKey ? (
                <Star
                  size={20}
                  className="text-yellow-400 mt-0.5 flex-shrink-0 fill-yellow-400"
                />
              ) : (
                <Check
                  size={20}
                  className="text-blue-400 mt-0.5 flex-shrink-0"
                />
              )}
              <span className={`text-sm ${feature.isKey ? 'text-foreground font-medium' : 'text-muted-foreground'}`}>
                {feature.name}
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* Valid Days */}
      {plan.valid_days && (
        <p className="text-sm text-muted-foreground mb-6 text-center">
          Valid for {plan.valid_days} days
        </p>
      )}

      {/* CTA Button */}
      <button
        onClick={handlePurchase}
        disabled={loading}
        className={`w-full py-4 px-6 rounded-xl font-semibold transition-all duration-300 flex items-center justify-center gap-2 ${
          isPopular
            ? 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-lg shadow-primary/30 disabled:opacity-50 disabled:cursor-not-allowed'
            : 'bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border hover:border-primary/50 disabled:opacity-50 disabled:cursor-not-allowed'
        }`}
      >
        {loading ? (
          <>
            <Loader2 className="h-5 w-5 animate-spin" />
            Processing...
          </>
        ) : (
          'Get Started'
        )}
      </button>
    </div>
  );
};

export default PricingCard;
