import React, { useEffect, useState } from 'react';
import { useFrappeGetCall } from 'frappe-react-sdk';
import PricingCard from './PricingCard';
import { Loader2 } from 'lucide-react';
import { SUBSCRIPTION_ENDPOINTS, API_CONFIG } from '../../../config/api.constants';

const PricingTiers = () => {
  const [plans, setPlans] = useState([]);

  const { data, isLoading, error } = useFrappeGetCall(
    SUBSCRIPTION_ENDPOINTS.GET_PLANS,
    {
      page: API_CONFIG.DEFAULT_PAGE,
      limit: API_CONFIG.DEFAULT_LIMIT,
      sort: 'view_order',
      order: 'asc'
    }
  );

  useEffect(() => {
    if (data?.message?.data) {
      setPlans(data.message.data);
    }
  }, [data]);

  if (isLoading) {
    return (
      <div className="py-20 px-4">
        <div className="max-w-7xl mx-auto flex items-center justify-center">
          <Loader2 className="w-12 h-12 text-primary animate-spin" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-20 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-destructive">Failed to load pricing plans. Please try again later.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Pricing Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {plans.map((plan, index) => (
            <PricingCard
              key={plan.name}
              plan={plan}
              isPopular={plan.name === 'Shared hosting'}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default PricingTiers;
