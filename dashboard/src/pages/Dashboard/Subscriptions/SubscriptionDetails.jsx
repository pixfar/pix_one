import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useFrappeGetCall, useFrappePostCall } from 'frappe-react-sdk';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Calendar,
  CreditCard,
  Key,
  Users,
  HardDrive,
  Building2,
  Activity,
  CheckCircle2,
  XCircle,
  Download,
  RotateCcw,
  AlertCircle,
  Copy,
  Loader2,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import {
  getSubscriptionDetails,
  getSubscriptionTransactions,
  cancelSubscription,
  renewSubscription,
  getStatusColor,
  getTransactionStatusColor,
  formatCurrency,
} from '@/services/subscription.service';
import { QUERY_KEYS } from '@/config/api.constants';
import { ROUTES } from '@/config/routes.constants';
import { format, differenceInDays } from 'date-fns';

const SubscriptionDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { call: getCall } = useFrappeGetCall();
  const { call: postCall } = useFrappePostCall();

  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [cancelImmediate, setCancelImmediate] = useState(false);

  // Fetch subscription details
  const {
    data: subscriptionData,
    isLoading: loadingSubscription,
    error: subscriptionError,
  } = useQuery({
    queryKey: [QUERY_KEYS.SUBSCRIPTION_DETAILS, id],
    queryFn: () => getSubscriptionDetails(getCall, id),
    staleTime: 1 * 60 * 1000,
  });

  const subscription = subscriptionData?.data;

  // Fetch transaction history
  const {
    data: transactionsData,
    isLoading: loadingTransactions,
  } = useQuery({
    queryKey: [QUERY_KEYS.MY_TRANSACTIONS, id],
    queryFn: () => getSubscriptionTransactions(getCall, id, { page: 1, limit: 10 }),
    enabled: !!id,
    staleTime: 1 * 60 * 1000,
  });

  const transactions = transactionsData?.data || [];

  // Renew mutation
  const renewMutation = useMutation({
    mutationFn: () => renewSubscription(postCall, id),
    onSuccess: (data) => {
      // Redirect to payment gateway
      if (data.paymentUrl) {
        window.location.href = data.paymentUrl;
      }
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to renew subscription');
    },
  });

  // Cancel mutation
  const cancelMutation = useMutation({
    mutationFn: (immediate) =>
      cancelSubscription(postCall, {
        subscription_id: id,
        reason: 'User initiated cancellation',
        immediate,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries([QUERY_KEYS.SUBSCRIPTION_DETAILS, id]);
      queryClient.invalidateQueries([QUERY_KEYS.MY_SUBSCRIPTIONS]);
      toast.success('Subscription cancelled successfully');
      setShowCancelDialog(false);
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to cancel subscription');
    },
  });

  const handleCopyLicenseKey = () => {
    if (subscription?.license_key) {
      navigator.clipboard.writeText(subscription.license_key);
      toast.success('License key copied to clipboard');
    }
  };

  const handleRenew = () => {
    renewMutation.mutate();
  };

  const handleCancel = () => {
    cancelMutation.mutate(cancelImmediate);
  };

  const calculateProgress = (current, max) => {
    return Math.min((current / max) * 100, 100);
  };

  const calculateDaysRemaining = () => {
    if (!subscription?.end_date) return 0;
    return differenceInDays(new Date(subscription.end_date), new Date());
  };

  if (loadingSubscription) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-7xl">
        <Skeleton className="h-10 w-32 mb-6" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Skeleton className="h-64" />
            <Skeleton className="h-96" />
          </div>
          <div className="space-y-6">
            <Skeleton className="h-48" />
            <Skeleton className="h-64" />
          </div>
        </div>
      </div>
    );
  }

  if (subscriptionError || !subscription) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-7xl">
        <Card className="border-red-200">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <XCircle className="h-12 w-12 text-red-600 mb-4" />
            <h3 className="text-lg font-semibold text-red-900 mb-2">Failed to Load Subscription</h3>
            <p className="text-muted-foreground mb-4">
              {subscriptionError?.message || 'Subscription not found'}
            </p>
            <Button onClick={() => navigate(ROUTES.SUBSCRIPTIONS)}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Subscriptions
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const daysRemaining = calculateDaysRemaining();
  const isExpiringSoon = daysRemaining <= 7 && daysRemaining >= 0;
  const canRenew = ['Expired', 'Past Due', 'Active'].includes(subscription.status);
  const canCancel = ['Active', 'Trial'].includes(subscription.status);

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <Button variant="ghost" onClick={() => navigate(ROUTES.SUBSCRIPTIONS)} className="mb-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Subscriptions
        </Button>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground mb-2">{subscription.plan_name}</h1>
            <Badge className={getStatusColor(subscription.status)} size="lg">
              {subscription.status}
            </Badge>
          </div>
          <div className="flex gap-2">
            {canRenew && (
              <Button onClick={handleRenew} disabled={renewMutation.isPending}>
                {renewMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <RotateCcw className="mr-2 h-4 w-4" />
                )}
                Renew Subscription
              </Button>
            )}
            {canCancel && (
              <AlertDialog open={showCancelDialog} onOpenChange={setShowCancelDialog}>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive">Cancel Subscription</Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Cancel Subscription?</AlertDialogTitle>
                    <AlertDialogDescription className="space-y-4">
                      <p>Are you sure you want to cancel your subscription?</p>
                      <div className="space-y-2">
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="radio"
                            name="cancelType"
                            checked={!cancelImmediate}
                            onChange={() => setCancelImmediate(false)}
                            className="h-4 w-4"
                          />
                          <div>
                            <p className="font-medium">Cancel at end of period</p>
                            <p className="text-sm text-muted-foreground">
                              Access until {format(new Date(subscription.end_date), 'MMM dd, yyyy')}
                            </p>
                          </div>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="radio"
                            name="cancelType"
                            checked={cancelImmediate}
                            onChange={() => setCancelImmediate(true)}
                            className="h-4 w-4"
                          />
                          <div>
                            <p className="font-medium">Cancel immediately</p>
                            <p className="text-sm text-muted-foreground">
                              Lose access immediately (no refund)
                            </p>
                          </div>
                        </label>
                      </div>
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Keep Subscription</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={handleCancel}
                      className="bg-red-600 hover:bg-red-700"
                      disabled={cancelMutation.isPending}
                    >
                      {cancelMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      Confirm Cancellation
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Expiring Soon Alert */}
          {isExpiringSoon && (
            <Card className="border-orange-200 bg-orange-50/50 dark:bg-orange-950/20">
              <CardContent className="flex items-center gap-3 py-4">
                <AlertCircle className="h-5 w-5 text-orange-600" />
                <div className="flex-1">
                  <p className="font-medium text-orange-900 dark:text-orange-100">
                    Subscription Expiring Soon
                  </p>
                  <p className="text-sm text-orange-800 dark:text-orange-200">
                    Your subscription will expire in {daysRemaining} days. Renew now to avoid service
                    interruption.
                  </p>
                </div>
                <Button size="sm" onClick={handleRenew} disabled={renewMutation.isPending}>
                  Renew Now
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Plan Details */}
          <Card>
            <CardHeader>
              <CardTitle>Subscription Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Plan Name</p>
                  <p className="font-medium">{subscription.plan_name}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Price</p>
                  <p className="font-medium">
                    {formatCurrency(subscription.price, subscription.currency)} /{' '}
                    {subscription.billing_interval}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1 flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    Start Date
                  </p>
                  <p className="font-medium">
                    {format(new Date(subscription.start_date), 'MMM dd, yyyy')}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1 flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    End Date
                  </p>
                  <p className="font-medium">{format(new Date(subscription.end_date), 'MMM dd, yyyy')}</p>
                </div>
              </div>

              {subscription.license_key && (
                <>
                  <Separator />
                  <div>
                    <p className="text-sm text-muted-foreground mb-2 flex items-center gap-1">
                      <Key className="h-4 w-4" />
                      License Key
                    </p>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 bg-muted px-4 py-2 rounded-md font-mono text-sm border border-border">
                        {subscription.license_key}
                      </code>
                      <Button variant="outline" size="sm" onClick={handleCopyLicenseKey}>
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Usage Statistics */}
          <Card>
            <CardHeader>
              <CardTitle>Resource Usage</CardTitle>
              <CardDescription>Current usage of your subscription resources</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Users */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Users</span>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {subscription.current_users || 0} / {subscription.max_users || 'Unlimited'}
                  </span>
                </div>
                {subscription.max_users > 0 && (
                  <Progress
                    value={calculateProgress(subscription.current_users || 0, subscription.max_users)}
                    className="h-2"
                  />
                )}
              </div>

              {/* Storage */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <div className="flex items-center gap-2">
                    <HardDrive className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Storage</span>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {subscription.current_storage_mb || 0}MB /{' '}
                    {subscription.max_storage_mb || 'Unlimited'}MB
                  </span>
                </div>
                {subscription.max_storage_mb > 0 && (
                  <Progress
                    value={calculateProgress(
                      subscription.current_storage_mb || 0,
                      subscription.max_storage_mb
                    )}
                    className="h-2"
                  />
                )}
              </div>

              {/* Companies */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <div className="flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Companies</span>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {subscription.current_companies || 0} / {subscription.max_companies || 'Unlimited'}
                  </span>
                </div>
                {subscription.max_companies > 0 && (
                  <Progress
                    value={calculateProgress(
                      subscription.current_companies || 0,
                      subscription.max_companies
                    )}
                    className="h-2"
                  />
                )}
              </div>
            </CardContent>
          </Card>

          {/* Payment History */}
          <Card>
            <CardHeader>
              <CardTitle>Payment History</CardTitle>
              <CardDescription>Recent transactions for this subscription</CardDescription>
            </CardHeader>
            <CardContent>
              {loadingTransactions ? (
                <div className="space-y-2">
                  {[...Array(3)].map((_, i) => (
                    <Skeleton key={i} className="h-12" />
                  ))}
                </div>
              ) : transactions.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">No transactions yet</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {transactions.map((transaction) => (
                      <TableRow key={transaction.name}>
                        <TableCell>
                          {format(new Date(transaction.payment_date || transaction.creation), 'MMM dd, yyyy')}
                        </TableCell>
                        <TableCell className="font-medium">
                          {formatCurrency(transaction.amount, transaction.currency)}
                        </TableCell>
                        <TableCell>{transaction.transaction_type}</TableCell>
                        <TableCell>
                          <Badge className={getTransactionStatusColor(transaction.status)}>
                            {transaction.status}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Stats */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Quick Stats</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Days Remaining</span>
                <span className="text-2xl font-bold">{daysRemaining > 0 ? daysRemaining : 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Total Paid</span>
                <span className="text-lg font-semibold">
                  {formatCurrency(subscription.total_amount_paid || 0, subscription.currency)}
                </span>
              </div>
              {subscription.auto_renew && (
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span>Auto-renewal enabled</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Plan Features */}
          {subscription.plan_features && subscription.plan_features.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Plan Features</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {subscription.plan_features.map((feature, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm">
                      <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <span>{feature.feature_name}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default SubscriptionDetails;
