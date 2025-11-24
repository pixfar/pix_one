import React from 'react';
import { Check, Star } from 'lucide-react';

const PricingCard = ({ plan, isPopular = false }) => {
  // Use features from API if available, otherwise use default list
  const features = plan.features && plan.features.length > 0
    ? plan.features.map(f => ({
        name: f.feature_name,
        isKey: f.is_key_feature === 1
      }))
    : [
        { name: 'All apps', isKey: false },
        { name: 'Unlimited users', isKey: false },
        { name: 'Unlimited support', isKey: false },
        { name: 'Hosting and maintenance', isKey: false }
      ];

  return (
    <div
      className={`relative flex flex-col bg-card border rounded-2xl p-8 transition-all duration-300 hover:shadow-2xl ${
        isPopular
          ? 'border-primary shadow-xl shadow-primary/20 scale-105'
          : 'border-border hover:border-primary/40'
      }`}
    >
      {/* Popular Badge */}
      {isPopular && (
        <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
          <span className="px-4 py-2 bg-primary text-primary-foreground text-sm font-semibold rounded-full shadow-lg">
            Most Popular
          </span>
        </div>
      )}

      {/* Plan Name */}
      <h3 className="text-2xl font-bold text-foreground mb-2">{plan.plan_name}</h3>

      {/* Price */}
      <div className="mb-6">
        <div className="flex items-baseline gap-2">
          <span className="text-5xl font-bold text-foreground">$</span>
          <span className="text-6xl font-bold text-foreground">
            {Math.floor(plan.price)}
          </span>
          <span className="text-2xl font-bold text-foreground">
            .{((plan.price % 1) * 100).toFixed(0).padStart(2, '0')}
          </span>
        </div>
        <p className="text-muted-foreground mt-2">/ user / month</p>
      </div>

      {/* Short Description */}
      <div className="mb-8">
        {plan.short_description?.split('\n').map((line, idx) => (
          <p key={idx} className="text-muted-foreground text-sm leading-relaxed">
            {line}
          </p>
        ))}
      </div>

      {/* Features List */}
      <div className="flex-1 mb-8">
        <ul className="space-y-4">
          {features.map((feature, idx) => (
            <li key={idx} className="flex items-start gap-3">
              {feature.isKey ? (
                <Star
                  size={20}
                  className="text-yellow-400 mt-0.5 flex-shrink-0 fill-yellow-400"
                />
              ) : (
                <Check
                  size={20}
                  className="text-blue-400 mt-0.5 flex-shrink-0"
                />
              )}
              <span className={`text-sm ${feature.isKey ? 'text-foreground font-medium' : 'text-muted-foreground'}`}>
                {feature.name}
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* Valid Days */}
      {plan.valid_days && (
        <p className="text-sm text-muted-foreground mb-6 text-center">
          Valid for {plan.valid_days} days
        </p>
      )}

      {/* CTA Button */}
      <button
        className={`w-full py-4 px-6 rounded-xl font-semibold transition-all duration-300 ${
          isPopular
            ? 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-lg shadow-primary/30'
            : 'bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border hover:border-primary/50'
        }`}
      >
        Get Started
      </button>
    </div>
  );
};

export default PricingCard;
