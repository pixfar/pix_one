import React, { useState } from 'react';

const PricingHero = () => {
  const [billingCycle, setBillingCycle] = useState('yearly');

  return (
    <div className="relative py-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 to-transparent pointer-events-none"></div>

      <div className="relative max-w-7xl mx-auto text-center">
        {/* Tagline */}
        <div className="inline-block mb-6">
          <span className="px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-400 text-sm font-medium">
            Transparent Pricing
          </span>
        </div>

        {/* Main Title - Home Page Style */}
        <div className="mb-8">
          <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold leading-tight">
            <span className="text-foreground">All the tech in</span>{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-blue-500 to-purple-500 drop-shadow-[0_0_30px_rgba(59,130,246,0.5)]">
              one platform
            </span>
          </h1>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mt-4">
            All your business on{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-500">
              one platform
            </span>
          </h2>
        </div>

        <p className="text-lg text-muted-foreground max-w-3xl mx-auto mb-12">
          All our plans include unlimited support, hosting and maintenance.<br />
          With no hidden costs, no limit on features or data: enjoy real transparency!
        </p>

        {/* Billing Toggle */}
        <div className="flex items-center justify-center gap-4 mb-16">
          <button
            onClick={() => setBillingCycle('yearly')}
            className={`px-6 py-3 rounded-xl font-medium transition-all duration-300 ${
              billingCycle === 'yearly'
                ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/30'
                : 'bg-muted text-muted-foreground hover:bg-muted/80'
            }`}
          >
            Yearly
          </button>
          <button
            onClick={() => setBillingCycle('monthly')}
            className={`px-6 py-3 rounded-xl font-medium transition-all duration-300 ${
              billingCycle === 'monthly'
                ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/30'
                : 'bg-muted text-muted-foreground hover:bg-muted/80'
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
