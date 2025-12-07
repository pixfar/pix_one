import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useFrappeGetCall } from 'frappe-react-sdk';
import { useQuery } from '@tanstack/react-query';
import {
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Calendar,
  CreditCard,
  Package,
  Loader2,
  Filter,
  ChevronRight,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { getMySubscriptions, getStatusColor, formatCurrency } from '@/services/subscription.service';
import { QUERY_KEYS } from '@/config/api.constants';
import { ROUTES } from '@/config/routes.constants';
import { format, differenceInDays } from 'date-fns';

const MySubscriptions = () => {
  const navigate = useNavigate();
  const { call } = useFrappeGetCall();
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(1);
  const limit = 10;

  // Fetch subscriptions with status filter
  const {
    data: subscriptionsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: [QUERY_KEYS.MY_SUBSCRIPTIONS, page, statusFilter],
    queryFn: () =>
      getMySubscriptions(call, {
        page,
        limit,
        status: statusFilter === 'all' ? null : statusFilter,
      }),
    staleTime: 2 * 60 * 1000,
  });

  const subscriptions = subscriptionsData?.data || [];
  const totalCount = subscriptionsData?.total || 0;
  const totalPages = Math.ceil(totalCount / limit);

  const handleViewDetails = (subscriptionId) => {
    navigate(`/dashboard/subscriptions/${subscriptionId}`);
  };

  const calculateDaysRemaining = (endDate) => {
    const today = new Date();
    const end = new Date(endDate);
    return differenceInDays(end, today);
  };

  const calculateProgress = (startDate, endDate) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const today = new Date();
    const total = differenceInDays(end, start);
    const elapsed = differenceInDays(today, start);
    return Math.min(Math.max((elapsed / total) * 100, 0), 100);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'Active':
        return <CheckCircle2 className="h-5 w-5 text-green-600" />;
      case 'Trial':
        return <Clock className="h-5 w-5 text-blue-600" />;
      case 'Expired':
        return <XCircle className="h-5 w-5 text-gray-600" />;
      case 'Cancelled':
        return <XCircle className="h-5 w-5 text-red-600" />;
      case 'Past Due':
        return <AlertCircle className="h-5 w-5 text-orange-600" />;
      default:
        return <AlertCircle className="h-5 w-5 text-yellow-600" />;
    }
  };

  // Status filter tabs
  const statusTabs = [
    { value: 'all', label: 'All', count: totalCount },
    { value: 'Active', label: 'Active' },
    { value: 'Trial', label: 'Trial' },
    { value: 'Past Due', label: 'Past Due' },
    { value: 'Expired', label: 'Expired' },
    { value: 'Cancelled', label: 'Cancelled' },
  ];

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-7xl">
        <Skeleton className="h-12 w-64 mb-6" />
        <Skeleton className="h-10 w-full mb-4" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-64" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-7xl">
        <Card className="border-red-200">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <XCircle className="h-12 w-12 text-red-600 mb-4" />
            <h3 className="text-lg font-semibold text-red-900 mb-2">Failed to Load Subscriptions</h3>
            <p className="text-muted-foreground mb-4">{error.message}</p>
            <Button onClick={() => refetch()}>Try Again</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">My Subscriptions</h1>
        <p className="text-muted-foreground">Manage your active and past subscriptions</p>
      </div>

      {/* Status Filter Tabs */}
      <Tabs value={statusFilter} onValueChange={setStatusFilter} className="mb-6">
        <TabsList className="grid w-full grid-cols-6 lg:w-auto lg:inline-grid">
          {statusTabs.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.label}
              {tab.count !== undefined && (
                <Badge variant="secondary" className="ml-2">
                  {tab.count}
                </Badge>
              )}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {/* Subscriptions Grid */}
      {subscriptions.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Package className="h-16 w-16 text-muted-foreground mb-4" />
            <h3 className="text-xl font-semibold mb-2">No Subscriptions Found</h3>
            <p className="text-muted-foreground mb-6">
              {statusFilter === 'all'
                ? "You don't have any subscriptions yet."
                : `No ${statusFilter.toLowerCase()} subscriptions found.`}
            </p>
            <Button onClick={() => navigate(ROUTES.PRICING)}>Browse Plans</Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {subscriptions.map((subscription) => {
              const daysRemaining = calculateDaysRemaining(subscription.end_date);
              const progress = calculateProgress(subscription.start_date, subscription.end_date);
              const isExpiringSoon = daysRemaining <= 7 && daysRemaining >= 0;

              return (
                <Card
                  key={subscription.name}
                  className={`hover:shadow-lg transition-all cursor-pointer ${
                    isExpiringSoon ? 'border-orange-200 bg-orange-50/30 dark:bg-orange-950/10' : ''
                  }`}
                  onClick={() => handleViewDetails(subscription.name)}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          {getStatusIcon(subscription.status)}
                          <CardTitle className="text-xl">{subscription.plan_name}</CardTitle>
                        </div>
                        <Badge className={getStatusColor(subscription.status)}>
                          {subscription.status}
                        </Badge>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-foreground">
                          {formatCurrency(subscription.price, subscription.currency)}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          /{subscription.billing_interval}
                        </p>
                      </div>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    {/* Date Information */}
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground flex items-center gap-1 mb-1">
                          <Calendar className="h-4 w-4" />
                          Start Date
                        </p>
                        <p className="font-medium">
                          {format(new Date(subscription.start_date), 'MMM dd, yyyy')}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground flex items-center gap-1 mb-1">
                          <Calendar className="h-4 w-4" />
                          End Date
                        </p>
                        <p className="font-medium">
                          {format(new Date(subscription.end_date), 'MMM dd, yyyy')}
                        </p>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    {subscription.status === 'Active' || subscription.status === 'Trial' ? (
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <p className="text-sm text-muted-foreground">Time Remaining</p>
                          <p className="text-sm font-medium">
                            {daysRemaining > 0 ? `${daysRemaining} days` : 'Expired'}
                          </p>
                        </div>
                        <Progress value={progress} className="h-2" />
                        {isExpiringSoon && (
                          <p className="text-xs text-orange-600 dark:text-orange-400 mt-2 flex items-center gap-1">
                            <AlertCircle className="h-3 w-3" />
                            Expiring soon! Please renew to avoid service interruption.
                          </p>
                        )}
                      </div>
                    ) : null}

                    {/* Action Button */}
                    <Button
                      className="w-full"
                      variant={subscription.status === 'Active' ? 'outline' : 'default'}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleViewDetails(subscription.name);
                      }}
                    >
                      View Details
                      <ChevronRight className="ml-2 h-4 w-4" />
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="outline"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default MySubscriptions;
