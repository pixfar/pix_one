import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { XCircle, AlertCircle, RefreshCw, ArrowLeft, HelpCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { toast } from 'sonner';
import { ROUTES } from '@/config/routes.constants';

const PaymentFailed = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const transactionId = searchParams.get('transaction');
  const reason = searchParams.get('reason') || 'Payment processing failed';
  const subscriptionId = searchParams.get('subscription');

  useEffect(() => {
    if (!transactionId) {
      toast.error('Invalid payment status');
    }
  }, [transactionId]);

  const handleRetryPayment = () => {
    if (subscriptionId) {
      // Navigate back to subscription with retry intent
      navigate(`/dashboard/subscriptions/${subscriptionId}?action=renew`);
    } else {
      // Navigate to pricing to start over
      navigate(ROUTES.PRICING);
    }
  };

  const handleBackToPricing = () => {
    navigate(ROUTES.PRICING);
  };

  const handleContactSupport = () => {
    // TODO: Implement support contact logic
    toast.info('Please contact support at support@pixone.com');
  };

  // Common failure reasons and their user-friendly messages
  const getFailureMessage = (reason) => {
    const reasonLower = reason.toLowerCase();

    if (reasonLower.includes('insufficient')) {
      return {
        title: 'Insufficient Funds',
        description: 'Your payment method does not have sufficient funds to complete this transaction.',
        suggestion: 'Please try a different payment method or add funds to your account.'
      };
    }

    if (reasonLower.includes('declined') || reasonLower.includes('card')) {
      return {
        title: 'Card Declined',
        description: 'Your card was declined by the bank.',
        suggestion: 'Please check your card details or try a different payment method.'
      };
    }

    if (reasonLower.includes('expired')) {
      return {
        title: 'Card Expired',
        description: 'The payment card has expired.',
        suggestion: 'Please update your payment method with a valid card.'
      };
    }

    if (reasonLower.includes('timeout') || reasonLower.includes('network')) {
      return {
        title: 'Network Timeout',
        description: 'The payment request timed out due to network issues.',
        suggestion: 'Please check your internet connection and try again.'
      };
    }

    // Default message
    return {
      title: 'Payment Failed',
      description: reason || 'We could not process your payment at this time.',
      suggestion: 'Please try again or contact support if the problem persists.'
    };
  };

  const failureInfo = getFailureMessage(reason);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-50 dark:from-gray-900 dark:to-gray-800 p-4">
      <Card className="w-full max-w-2xl shadow-2xl border-red-200 dark:border-red-900">
        <CardHeader className="text-center pb-6">
          <div className="flex justify-center mb-4">
            <div className="bg-red-100 dark:bg-red-900/30 rounded-full p-4">
              <XCircle className="h-16 w-16 text-red-600 dark:text-red-400" />
            </div>
          </div>
          <CardTitle className="text-3xl font-bold text-red-700 dark:text-red-400">
            {failureInfo.title}
          </CardTitle>
          <CardDescription className="text-lg mt-2">
            {failureInfo.description}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Failure Details Alert */}
          <Alert variant="destructive" className="bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-900">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>What happened?</AlertTitle>
            <AlertDescription className="mt-2">
              {failureInfo.suggestion}
            </AlertDescription>
          </Alert>

          <Separator />

          {/* Transaction Information */}
          {transactionId && (
            <div className="bg-muted/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold text-muted-foreground">Transaction Details</h3>
                <Badge variant="destructive" className="bg-red-100 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-400">
                  Failed
                </Badge>
              </div>
              <div className="text-sm">
                <span className="text-muted-foreground">Transaction ID: </span>
                <span className="font-mono">{transactionId}</span>
              </div>
              <div className="text-sm mt-1 text-muted-foreground">
                {new Date().toLocaleString('en-US', {
                  dateStyle: 'medium',
                  timeStyle: 'short'
                })}
              </div>
            </div>
          )}

          {/* Common Issues & Solutions */}
          <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900 rounded-lg p-4">
            <div className="flex items-start gap-2 mb-3">
              <HelpCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              <h4 className="font-semibold text-blue-900 dark:text-blue-100">
                Common Issues & Solutions
              </h4>
            </div>
            <ul className="space-y-2 text-sm text-blue-800 dark:text-blue-200 ml-7">
              <li className="flex items-start gap-2">
                <span className="font-medium">•</span>
                <span>Double-check your card number, expiry date, and CVV</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="font-medium">•</span>
                <span>Ensure your billing address matches your card records</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="font-medium">•</span>
                <span>Verify that your card is enabled for online transactions</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="font-medium">•</span>
                <span>Check if you have sufficient funds or credit limit</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="font-medium">•</span>
                <span>Try using a different payment method or card</span>
              </li>
            </ul>
          </div>

          <Separator />

          {/* Action Buttons */}
          <div className="space-y-3">
            <Button
              onClick={handleRetryPayment}
              className="w-full bg-primary hover:bg-primary/90"
              size="lg"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Try Again with Different Payment Method
            </Button>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Button
                onClick={handleBackToPricing}
                variant="outline"
                size="lg"
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Pricing
              </Button>
              <Button
                onClick={handleContactSupport}
                variant="outline"
                size="lg"
              >
                <HelpCircle className="mr-2 h-4 w-4" />
                Contact Support
              </Button>
            </div>
          </div>

          {/* Additional Help */}
          <div className="text-center text-sm text-muted-foreground pt-2">
            <p>Need help? Contact our support team at</p>
            <a
              href="mailto:support@pixone.com"
              className="text-primary hover:underline font-medium"
            >
              support@pixone.com
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PaymentFailed;
