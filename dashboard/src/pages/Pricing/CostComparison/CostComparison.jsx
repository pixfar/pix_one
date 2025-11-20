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
    <div className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-transparent to-blue-500/5">
      <div className="max-w-7xl mx-auto">
        {/* Section Title */}
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Cut costs with Odoo
          </h2>
          <p className="text-gray-400 text-lg">
            Cost savings based on average price per user for each app.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          {/* Left Column: App Selection */}
          <div className="bg-white/5 border border-white/10 rounded-2xl p-8">
            <h3 className="text-xl font-bold text-white mb-6">
              Which apps do you use?
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-6">
              {Object.keys(appPrices).map((app) => (
                <button
                  key={app}
                  onClick={() => toggleApp(app)}
                  className={`py-3 px-4 rounded-xl font-medium transition-all duration-300 text-sm ${
                    selectedApps[app]
                      ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30'
                      : 'bg-white/5 text-gray-300 hover:bg-white/10 border border-white/10'
                  }`}
                >
                  {app}
                </button>
              ))}
            </div>

            <div className="mt-8">
              <label className="block text-white font-medium mb-4">
                How many users?
              </label>
              <input
                type="range"
                min="1"
                max="100"
                value={users}
                onChange={(e) => setUsers(parseInt(e.target.value))}
                className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer slider-thumb"
              />
              <div className="flex justify-between items-center mt-2">
                <span className="text-gray-400 text-sm">1</span>
                <span className="text-3xl font-bold text-blue-400">{users}</span>
                <span className="text-gray-400 text-sm">100</span>
              </div>
            </div>
          </div>

          {/* Right Column: Cost Comparison */}
          <div className="space-y-6">
            {/* Competitor Costs */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-8">
              <h3 className="text-xl font-bold text-white mb-6">
                Apps to replace
                <span className="text-gray-400 font-normal text-sm ml-2">
                  for {users} users / month
                </span>
              </h3>

              {selectedAppsArray.length > 0 ? (
                <div className="space-y-3 mb-6">
                  {selectedAppsArray.map((app) => (
                    <div
                      key={app}
                      className="flex items-center justify-between py-2 px-4 bg-white/5 rounded-lg"
                    >
                      <span className="text-gray-300">{appPrices[app].name}</span>
                      <span className="text-white font-semibold">
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
                <p className="text-gray-400 text-center py-8">
                  Select apps to see comparison
                </p>
              )}

              <div className="pt-6 border-t border-white/10">
                <div className="flex items-center justify-between">
                  <span className="text-xl font-bold text-white">TOTAL</span>
                  <span className="text-2xl font-bold text-red-400">
                    ${competitorCost.toLocaleString()}.00 / year
                  </span>
                </div>
              </div>
            </div>

            {/* Odoo Costs */}
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-2xl p-8">
              <h3 className="text-xl font-bold text-white mb-6">
                All Odoo Apps
                <span className="text-gray-400 font-normal text-sm ml-2">
                  for {users} users
                </span>
              </h3>

              <div className="py-8 text-center mb-6">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-500 rounded-full mb-4">
                  <Check size={32} className="text-white" />
                </div>
                <p className="text-gray-300">
                  All selected apps included in one plan
                </p>
              </div>

              <div className="pt-6 border-t border-blue-500/30">
                <div className="flex items-center justify-between">
                  <span className="text-xl font-bold text-white">TOTAL</span>
                  <span className="text-2xl font-bold text-green-400">
                    ${odooCost.toLocaleString()}.00 / year
                  </span>
                </div>
              </div>
            </div>

            {/* Savings */}
            {competitorCost > 0 && (
              <div className="bg-gradient-to-r from-green-500/20 to-blue-500/20 border border-green-500/30 rounded-2xl p-8">
                <div className="text-center">
                  <p className="text-gray-300 mb-2">Your savings</p>
                  <p className="text-4xl font-bold text-green-400">
                    ${(competitorCost - odooCost).toLocaleString()}.00 / year
                  </p>
                  <p className="text-gray-400 text-sm mt-4">
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
          background: #3b82f6;
          border-radius: 50%;
          cursor: pointer;
          box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
        }
        input[type='range']::-moz-range-thumb {
          width: 20px;
          height: 20px;
          background: #3b82f6;
          border-radius: 50%;
          cursor: pointer;
          border: none;
          box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
        }
      `}</style>
    </div>
  );
};

export default CostComparison;
