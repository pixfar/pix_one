import React from 'react';
import { Check } from 'lucide-react';

const PricingCard = ({ plan, isPopular = false }) => {
  const features = [
    'All apps',
    'Odoo Online',
    'Unlimited users',
    'Unlimited support',
    'Hosting and maintenance',
    'No hidden costs',
    'No limit on features',
    'No limit on data'
  ];

  return (
    <div
      className={`relative flex flex-col bg-white/5 border rounded-2xl p-8 transition-all duration-300 hover:shadow-2xl ${
        isPopular
          ? 'border-blue-500 shadow-xl shadow-blue-500/20 scale-105'
          : 'border-white/10 hover:border-blue-500/40'
      }`}
    >
      {/* Popular Badge */}
      {isPopular && (
        <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
          <span className="px-4 py-2 bg-blue-500 text-white text-sm font-semibold rounded-full shadow-lg">
            Most Popular
          </span>
        </div>
      )}

      {/* Plan Name */}
      <h3 className="text-2xl font-bold text-white mb-2">{plan.plan_name}</h3>

      {/* Price */}
      <div className="mb-6">
        <div className="flex items-baseline gap-2">
          <span className="text-5xl font-bold text-white">$</span>
          <span className="text-6xl font-bold text-white">
            {Math.floor(plan.price)}
          </span>
          <span className="text-2xl font-bold text-white">
            .{((plan.price % 1) * 100).toFixed(0).padStart(2, '0')}
          </span>
        </div>
        <p className="text-gray-400 mt-2">/ user / month</p>
      </div>

      {/* Short Description */}
      <div className="mb-8">
        {plan.short_description?.split('\n').map((line, idx) => (
          <p key={idx} className="text-gray-300 text-sm leading-relaxed">
            {line}
          </p>
        ))}
      </div>

      {/* Features List */}
      <div className="flex-1 mb-8">
        <ul className="space-y-4">
          {features.map((feature, idx) => (
            <li key={idx} className="flex items-start gap-3">
              <Check
                size={20}
                className="text-blue-400 mt-0.5 flex-shrink-0"
              />
              <span className="text-gray-300 text-sm">{feature}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Valid Days */}
      {plan.valid_days && (
        <p className="text-sm text-gray-400 mb-6 text-center">
          Valid for {plan.valid_days} days
        </p>
      )}

      {/* CTA Button */}
      <button
        className={`w-full py-4 px-6 rounded-xl font-semibold transition-all duration-300 ${
          isPopular
            ? 'bg-blue-500 text-white hover:bg-blue-600 shadow-lg shadow-blue-500/30'
            : 'bg-white/10 text-white hover:bg-white/20 border border-white/20 hover:border-blue-500/50'
        }`}
      >
        Get Started
      </button>
    </div>
  );
};

export default PricingCard;
