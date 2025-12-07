import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Ban, Info, RotateCcw, ArrowLeft, MessageCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { toast } from 'sonner';
import { ROUTES } from '@/config/routes.constants';

const PaymentCancelled = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const transactionId = searchParams.get('transaction');
  const subscriptionId = searchParams.get('subscription');
  const planName = searchParams.get('plan');

  const [countdown, setCountdown] = useState(15);

  useEffect(() => {
    if (!transactionId) {
      toast.error('Invalid payment cancellation');
    }

    // Auto-redirect to pricing after 15 seconds
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          navigate(ROUTES.PRICING);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [transactionId, navigate]);

  const handleRetryPayment = () => {
    if (subscriptionId) {
      navigate(`/dashboard/subscriptions/${subscriptionId}?action=renew`);
    } else {
      navigate(ROUTES.PRICING);
    }
  };

  const handleBackToPricing = () => {
    navigate(ROUTES.PRICING);
  };

  const handleViewPlans = () => {
    navigate(ROUTES.PRICING);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-50 to-yellow-50 dark:from-gray-900 dark:to-gray-800 p-4">
      <Card className="w-full max-w-2xl shadow-2xl border-orange-200 dark:border-orange-900">
        <CardHeader className="text-center pb-6">
          <div className="flex justify-center mb-4">
            <div className="bg-orange-100 dark:bg-orange-900/30 rounded-full p-4">
              <Ban className="h-16 w-16 text-orange-600 dark:text-orange-400" />
            </div>
          </div>
          <CardTitle className="text-3xl font-bold text-orange-700 dark:text-orange-400">
            Payment Cancelled
          </CardTitle>
          <CardDescription className="text-lg mt-2">
            You cancelled the payment process
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Information Alert */}
          <Alert className="bg-orange-50 dark:bg-orange-950/30 border-orange-200 dark:border-orange-900">
            <Info className="h-4 w-4 text-orange-600" />
            <AlertTitle className="text-orange-900 dark:text-orange-100">
              No charges were made
            </AlertTitle>
            <AlertDescription className="mt-2 text-orange-800 dark:text-orange-200">
              Your payment was cancelled before any charges were processed. You can try again whenever you're ready.
            </AlertDescription>
          </Alert>

          <Separator />

          {/* Transaction Information */}
          {transactionId && (
            <div className="bg-muted/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold text-muted-foreground">Transaction Details</h3>
                <Badge variant="outline" className="bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-900/30 dark:text-orange-400">
                  Cancelled
                </Badge>
              </div>
              <div className="space-y-1">
                <div className="text-sm">
                  <span className="text-muted-foreground">Transaction ID: </span>
                  <span className="font-mono">{transactionId}</span>
                </div>
                {planName && (
                  <div className="text-sm">
                    <span className="text-muted-foreground">Plan: </span>
                    <span className="font-medium">{planName}</span>
                  </div>
                )}
                <div className="text-sm text-muted-foreground">
                  {new Date().toLocaleString('en-US', {
                    dateStyle: 'medium',
                    timeStyle: 'short'
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Why did this happen? */}
          <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900 rounded-lg p-4">
            <div className="flex items-start gap-2 mb-3">
              <MessageCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
                  Common reasons for cancellation:
                </h4>
                <ul className="space-y-2 text-sm text-blue-800 dark:text-blue-200">
                  <li className="flex items-start gap-2">
                    <span className="font-medium">•</span>
                    <span>Clicked the back button or closed the payment window</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="font-medium">•</span>
                    <span>Decided to review the plan details before purchasing</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="font-medium">•</span>
                    <span>Want to compare different subscription options</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="font-medium">•</span>
                    <span>Need to check with your team before proceeding</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          {/* What's Next? */}
          <div className="bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-900 rounded-lg p-4">
            <h4 className="font-semibold text-green-900 dark:text-green-100 mb-2">
              What would you like to do next?
            </h4>
            <p className="text-sm text-green-800 dark:text-green-200">
              You can review our pricing plans, compare features, or restart the payment process when you're ready. Your subscription details are still saved and waiting for you.
            </p>
          </div>

          <Separator />

          {/* Action Buttons */}
          <div className="space-y-3">
            <Button
              onClick={handleRetryPayment}
              className="w-full bg-primary hover:bg-primary/90"
              size="lg"
            >
              <RotateCcw className="mr-2 h-4 w-4" />
              Complete Payment Now
            </Button>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Button
                onClick={handleViewPlans}
                variant="outline"
                size="lg"
              >
                View All Plans
              </Button>
              <Button
                onClick={handleBackToPricing}
                variant="outline"
                size="lg"
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Pricing
              </Button>
            </div>
          </div>

          {/* Auto-redirect Notice */}
          <div className="text-center text-sm text-muted-foreground pt-2 border-t border-border">
            <p>Redirecting to pricing page in {countdown} seconds...</p>
            <button
              onClick={() => {
                setCountdown(0);
                navigate(ROUTES.PRICING);
              }}
              className="text-primary hover:underline mt-1"
            >
              Go now
            </button>
          </div>

          {/* Help Section */}
          <div className="text-center text-sm text-muted-foreground">
            <p>Have questions about our plans?</p>
            <a
              href="mailto:sales@pixone.com"
              className="text-primary hover:underline font-medium"
            >
              Contact Sales
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PaymentCancelled;
