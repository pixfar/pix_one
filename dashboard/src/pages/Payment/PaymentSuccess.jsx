import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CheckCircle2, Loader2, ArrowRight, Download } from 'lucide-react';
import { useFrappeGetCall } from 'frappe-react-sdk';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { getSubscriptionDetails } from '@/services/subscription.service';
import { QUERY_KEYS } from '@/config/api.constants';
import { ROUTES } from '@/config/routes.constants';

const PaymentSuccess = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { call } = useFrappeGetCall();

  const subscriptionId = searchParams.get('subscription');
  const transactionId = searchParams.get('transaction');

  const [countdown, setCountdown] = useState(10);

  // Fetch subscription details
  const { data: subscriptionData, isLoading, error } = useQuery({
    queryKey: [QUERY_KEYS.SUBSCRIPTION_DETAILS, subscriptionId],
    queryFn: () => getSubscriptionDetails(call, subscriptionId),
    enabled: !!subscriptionId,
    staleTime: 1 * 60 * 1000,
    retry: 2
  });

  const subscription = subscriptionData?.data;

  // Auto-redirect countdown
  useEffect(() => {
    if (!subscriptionId) {
      toast.error('Invalid payment confirmation');
      navigate(ROUTES.PRICING);
      return;
    }

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          navigate(`/dashboard/subscriptions/${subscriptionId}`);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [subscriptionId, navigate]);

  // Handle manual navigation
  const handleViewSubscription = () => {
    navigate(`/dashboard/subscriptions/${subscriptionId}`);
  };

  const handleBackToDashboard = () => {
    navigate(ROUTES.DASHBOARD);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-emerald-50 dark:from-gray-900 dark:to-gray-800">
        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
            <p className="text-muted-foreground">Loading subscription details...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    toast.error('Failed to load subscription details');
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-emerald-50 dark:from-gray-900 dark:to-gray-800 p-4">
      <Card className="w-full max-w-2xl shadow-2xl border-green-200 dark:border-green-900">
        <CardHeader className="text-center pb-6">
          <div className="flex justify-center mb-4">
            <div className="bg-green-100 dark:bg-green-900/30 rounded-full p-4">
              <CheckCircle2 className="h-16 w-16 text-green-600 dark:text-green-400" />
            </div>
          </div>
          <CardTitle className="text-3xl font-bold text-green-700 dark:text-green-400">
            Payment Successful!
          </CardTitle>
          <CardDescription className="text-lg mt-2">
            Your subscription has been activated successfully
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Subscription Details */}
          {subscription && (
            <div className="space-y-4">
              <Separator />

              <div className="bg-muted/50 rounded-lg p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Subscription Details</h3>
                  <Badge className="bg-green-100 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-400">
                    {subscription.status}
                  </Badge>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Plan</p>
                    <p className="font-medium">{subscription.plan_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Amount Paid</p>
                    <p className="font-medium">
                      {subscription.currency} {parseFloat(subscription.price).toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Start Date</p>
                    <p className="font-medium">
                      {new Date(subscription.start_date).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">End Date</p>
                    <p className="font-medium">
                      {new Date(subscription.end_date).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })}
                    </p>
                  </div>
                </div>

                {subscription.license_key && (
                  <div className="pt-4 border-t border-border">
                    <p className="text-sm text-muted-foreground mb-2">License Key</p>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 bg-background px-4 py-2 rounded-md font-mono text-sm border border-border">
                        {subscription.license_key}
                      </code>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          navigator.clipboard.writeText(subscription.license_key);
                          toast.success('License key copied to clipboard');
                        }}
                      >
                        Copy
                      </Button>
                    </div>
                  </div>
                )}
              </div>

              {transactionId && (
                <div className="text-sm text-muted-foreground text-center">
                  Transaction ID: <span className="font-mono">{transactionId}</span>
                </div>
              )}
            </div>
          )}

          <Separator />

          {/* Next Steps */}
          <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900 rounded-lg p-4">
            <h4 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
              What's Next?
            </h4>
            <ul className="space-y-2 text-sm text-blue-800 dark:text-blue-200">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>Check your email for subscription confirmation and license details</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>Access your subscription dashboard to manage your plan</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>Use your license key to activate Pix One on your instance</span>
              </li>
            </ul>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3">
            <Button
              onClick={handleViewSubscription}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white"
              size="lg"
            >
              View Subscription Details
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <Button
              onClick={handleBackToDashboard}
              variant="outline"
              size="lg"
              className="flex-1"
            >
              Go to Dashboard
            </Button>
          </div>

          {/* Auto-redirect Notice */}
          <div className="text-center text-sm text-muted-foreground">
            Redirecting to subscription details in {countdown} seconds...
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PaymentSuccess;
