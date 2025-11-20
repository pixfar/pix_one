import React, { useState } from 'react';

const PricingHero = () => {
  const [billingCycle, setBillingCycle] = useState('yearly');

  return (
    <div className="relative py-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 to-transparent pointer-events-none"></div>

      <div className="relative max-w-7xl mx-auto text-center">
        {/* Tagline */}
        <div className="inline-block mb-4">
          <span className="px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-400 text-sm font-medium">
            You are not dreaming!
          </span>
        </div>

        {/* Main Title */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-8">
          Choose Your Perfect Plan
        </h1>

        <p className="text-lg text-gray-400 max-w-3xl mx-auto mb-12">
          All our plans include unlimited support, hosting and maintenance.<br />
          With no hidden costs, no limit on features or data: enjoy real transparency!
        </p>

        {/* Billing Toggle */}
        <div className="flex items-center justify-center gap-4 mb-16">
          <button
            onClick={() => setBillingCycle('yearly')}
            className={`px-6 py-3 rounded-xl font-medium transition-all duration-300 ${
              billingCycle === 'yearly'
                ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30'
                : 'bg-white/5 text-gray-400 hover:bg-white/10'
            }`}
          >
            Yearly
          </button>
          <button
            onClick={() => setBillingCycle('monthly')}
            className={`px-6 py-3 rounded-xl font-medium transition-all duration-300 ${
              billingCycle === 'monthly'
                ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30'
                : 'bg-white/5 text-gray-400 hover:bg-white/10'
            }`}
          >
            Monthly
          </button>
        </div>
      </div>
    </div>
  );
};

export default PricingHero;
