import React, { useState, useEffect } from 'react';
import { Check } from 'lucide-react';

const CostComparison = () => {
  const [selectedApps, setSelectedApps] = useState({
    Project: false,
    Accounting: false,
    eCommerce: false,
    CRM: false,
    Discuss: false,
    Knowledge: false,
    HR: false,
    Sign: false,
    Inventory: false,
    Website: false,
    Documents: false,
    PoS: false,
    Expenses: false,
    Appointment: false,
    Purchase: false,
    Social: false,
    Planning: false,
    Emailing: false,
    Timesheet: false,
    Helpdesk: false,
    Events: false,
    MRP: false,
    Rental: false
  });

  const [users, setUsers] = useState(20);
  const [competitorCost, setCompetitorCost] = useState(0);
  const [odooCost, setOdooCost] = useState(0);

  const appPrices = {
    Project: { name: 'Asana', price: 20 },
    Accounting: { name: 'Quickbooks', price: 76 },
    eCommerce: { name: 'Shopify', price: 79 },
    CRM: { name: 'Salesforce', price: 165 },
    Discuss: { name: 'Slack', price: 14.10 },
    Knowledge: { name: 'Notion', price: 14 },
    HR: { name: 'BambooHR', price: 8 },
    Sign: { name: 'Docusign', price: 38 },
    Inventory: { name: 'Fishbowl', price: 45 },
    Website: { name: 'Wordpress', price: 25 },
    Documents: { name: 'Google Workspace', price: 12 },
    PoS: { name: 'Square', price: 60 },
    Expenses: { name: 'Expensify', price: 9 },
    Appointment: { name: 'Calendly', price: 12 },
    Purchase: { name: 'Coupa', price: 50 },
    Social: { name: 'Hootsuite', price: 49 },
    Planning: { name: 'Monday.com', price: 24 },
    Emailing: { name: 'Mailchimp', price: 299 },
    Timesheet: { name: 'Harvest', price: 12 },
    Helpdesk: { name: 'Zendesk', price: 55 },
    Events: { name: 'Eventbrite', price: 79 },
    MRP: { name: 'NetSuite', price: 99 },
    Rental: { name: 'Rentle', price: 149 }
  };

  useEffect(() => {
    let total = 0;
    Object.keys(selectedApps).forEach((app) => {
      if (selectedApps[app]) {
        const perUser = appPrices[app].price;
        if (app === 'Website' || app === 'eCommerce' || app === 'Emailing') {
          total += perUser;
        } else {
          total += perUser * users;
        }
      }
    });
    setCompetitorCost(total * 12);

    const selectedCount = Object.values(selectedApps).filter(Boolean).length;
    if (selectedCount > 0) {
      setOdooCost(7.25 * users * 12);
    } else {
      setOdooCost(0);
    }
  }, [selectedApps, users]);

  const toggleApp = (app) => {
    setSelectedApps((prev) => ({
      ...prev,
      [app]: !prev[app]
    }));
  };

  const selectedAppsArray = Object.keys(selectedApps).filter(
    (app) => selectedApps[app]
  );

  return (
    <div className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-transparent to-primary/5">
      <div className="max-w-7xl mx-auto">
        {/* Section Title */}
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
            Cut costs with Odoo
          </h2>
          <p className="text-muted-foreground text-lg">
            Cost savings based on average price per user for each app.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          {/* Left Column: App Selection */}
          <div className="bg-card/50 border border-border rounded-2xl p-8">
            <h3 className="text-xl font-bold text-foreground mb-6">
              Which apps do you use?
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-6">
              {Object.keys(appPrices).map((app) => (
                <button
                  key={app}
                  onClick={() => toggleApp(app)}
                  className={`py-3 px-4 rounded-xl font-medium transition-all duration-300 text-sm ${
                    selectedApps[app]
                      ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/30'
                      : 'bg-card text-muted-foreground hover:bg-surface-hover border border-border'
                  }`}
                >
                  {app}
                </button>
              ))}
            </div>

            <div className="mt-8">
              <label className="block text-foreground font-medium mb-4">
                How many users?
              </label>
              <input
                type="range"
                min="1"
                max="100"
                value={users}
                onChange={(e) => setUsers(parseInt(e.target.value))}
                className="w-full h-2 bg-surface rounded-lg appearance-none cursor-pointer slider-thumb"
              />
              <div className="flex justify-between items-center mt-2">
                <span className="text-muted-foreground text-sm">1</span>
                <span className="text-3xl font-bold text-primary">{users}</span>
                <span className="text-muted-foreground text-sm">100</span>
              </div>
            </div>
          </div>

          {/* Right Column: Cost Comparison */}
          <div className="space-y-6">
            {/* Competitor Costs */}
            <div className="bg-card/50 border border-border rounded-2xl p-8">
              <h3 className="text-xl font-bold text-foreground mb-6">
                Apps to replace
                <span className="text-muted-foreground font-normal text-sm ml-2">
                  for {users} users / month
                </span>
              </h3>

              {selectedAppsArray.length > 0 ? (
                <div className="space-y-3 mb-6">
                  {selectedAppsArray.map((app) => (
                    <div
                      key={app}
                      className="flex items-center justify-between py-2 px-4 bg-surface rounded-lg"
                    >
                      <span className="text-muted-foreground">{appPrices[app].name}</span>
                      <span className="text-foreground font-semibold">
                        ${' '}
                        {['Website', 'eCommerce', 'Emailing'].includes(app)
                          ? appPrices[app].price
                          : appPrices[app].price}{' '}
                        {['Website', 'eCommerce', 'Emailing'].includes(app)
                          ? ''
                          : '/ user'}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-center py-8">
                  Select apps to see comparison
                </p>
              )}

              <div className="pt-6 border-t border-border">
                <div className="flex items-center justify-between">
                  <span className="text-xl font-bold text-foreground">TOTAL</span>
                  <span className="text-2xl font-bold text-destructive">
                    ${competitorCost.toLocaleString()}.00 / year
                  </span>
                </div>
              </div>
            </div>

            {/* Odoo Costs */}
            <div className="bg-primary/10 border border-primary/30 rounded-2xl p-8">
              <h3 className="text-xl font-bold text-foreground mb-6">
                All Odoo Apps
                <span className="text-muted-foreground font-normal text-sm ml-2">
                  for {users} users
                </span>
              </h3>

              <div className="py-8 text-center mb-6">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-primary rounded-full mb-4">
                  <Check size={32} className="text-primary-foreground" />
                </div>
                <p className="text-muted-foreground">
                  All selected apps included in one plan
                </p>
              </div>

              <div className="pt-6 border-t border-primary/30">
                <div className="flex items-center justify-between">
                  <span className="text-xl font-bold text-foreground">TOTAL</span>
                  <span className="text-2xl font-bold text-[color:var(--brand-teal)]">
                    ${odooCost.toLocaleString()}.00 / year
                  </span>
                </div>
              </div>
            </div>

            {/* Savings */}
            {competitorCost > 0 && (
              <div className="bg-gradient-to-r from-[color:var(--brand-teal)]/20 to-primary/20 border border-[color:var(--brand-teal)]/30 rounded-2xl p-8">
                <div className="text-center">
                  <p className="text-muted-foreground mb-2">Your savings</p>
                  <p className="text-4xl font-bold text-[color:var(--brand-teal)]">
                    ${(competitorCost - odooCost).toLocaleString()}.00 / year
                  </p>
                  <p className="text-muted-foreground text-sm mt-4">
                    For a fully-integrated software.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <style>{`
        input[type='range']::-webkit-slider-thumb {
          appearance: none;
          width: 20px;
          height: 20px;
          background: var(--color-primary);
          border-radius: 50%;
          cursor: pointer;
          box-shadow: 0 0 10px oklch(from var(--color-primary) l c h / 0.5);
        }
        input[type='range']::-moz-range-thumb {
          width: 20px;
          height: 20px;
          background: var(--color-primary);
          border-radius: 50%;
          cursor: pointer;
          border: none;
          box-shadow: 0 0 10px oklch(from var(--color-primary) l c h / 0.5);
        }
      `}</style>
    </div>
  );
};

export default CostComparison;
