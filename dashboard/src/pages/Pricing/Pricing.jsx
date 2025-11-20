import React from 'react';
import PricingHero from './PricingHero/PricingHero';
import PricingTiers from './PricingTiers/PricingTiers';
import CostComparison from './CostComparison/CostComparison';
import FAQ from './FAQ/FAQ';

const Pricing = () => {
  return (
    <div className='min-h-screen'>
      <PricingHero />
      <PricingTiers />
      <CostComparison />
      <FAQ />
    </div>
  );
};

export default Pricing;
