import React, { useEffect, useState } from 'react';
import { useFrappeGetCall } from 'frappe-react-sdk';
import PricingCard from './PricingCard';
import { Loader2 } from 'lucide-react';

const PricingTiers = () => {
  const [plans, setPlans] = useState([]);

  const { data, isLoading, error } = useFrappeGetCall(
    'pix_one.api.subscription_plans.get_plans.get_plans.get_subscription_plans',
    {
      page: 1,
      limit: 10,
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
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-20 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-red-400">Failed to load pricing plans. Please try again later.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Pricing Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-20">
          {plans.map((plan, index) => (
            <PricingCard
              key={plan.name}
              plan={plan}
              isPopular={plan.plan_name === 'Standard'}
            />
          ))}
        </div>

        {/* Included Apps Section */}
        <div className="bg-white/5 border border-white/10 rounded-2xl p-8 sm:p-12">
          <h3 className="text-2xl font-bold text-white text-center mb-8">
            The Standard and Custom plans include all apps for a single fee:
          </h3>

          {/* Apps Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6 mb-8">
            {[
              'Sales',
              'eCommerce',
              'Sign',
              'Website',
              'Accounting',
              'CRM',
              'Inventory',
              'HR',
              'Project',
              'POS'
            ].map((app) => (
              <div
                key={app}
                className="flex items-center justify-center py-3 px-4 bg-blue-500/10 border border-blue-500/20 rounded-xl hover:bg-blue-500/20 transition-all duration-300"
              >
                <span className="text-blue-400 font-medium text-sm">{app}</span>
              </div>
            ))}
          </div>

          <p className="text-center text-gray-400 text-lg font-medium">
            And many more
          </p>
        </div>

        {/* Disclaimer */}
        <div className="mt-12 text-center space-y-2">
          <p className="text-sm text-gray-400">
            (*) The discount is valid for 12 months, for initial users ordered.
          </p>
          <p className="text-sm text-gray-400">
            (**) Cost for Odoo.sh hosting not included.
          </p>
        </div>
      </div>
    </div>
  );
};

export default PricingTiers;
