import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

const FAQ = () => {
  const [openIndex, setOpenIndex] = useState(null);

  const faqs = [
    {
      question: 'Do I really have access to hundreds of apps and modules for a single price?',
      answer:
        "Yes! With our Standard and Custom plans, you get access to all Odoo apps for a single price per user. There are no additional fees for adding more apps or modules. You can use as many or as few apps as you need, all included in your subscription."
    },
    {
      question: "What's included in the subscription?",
      answer:
        'Your subscription includes unlimited access to all apps, hosting, regular updates, maintenance, security patches, unlimited support, and unlimited data storage. There are no hidden costs or surprise fees.'
    },
    {
      question: 'What is On-premise / Odoo.sh?',
      answer:
        'On-premise means you host the software on your own servers, giving you complete control over your data and infrastructure. Odoo.sh is our Platform-as-a-Service (PaaS) solution that provides additional features like staging environments, automated backups, and advanced deployment options. Note that Odoo.sh has separate hosting costs.'
    },
    {
      question: 'Where can I get implementation services, and how much does it cost?',
      answer:
        'Implementation services are available through our certified partners or our professional services team. Costs vary depending on your business requirements, the complexity of your setup, and the number of apps you need to implement. Contact our sales team for a customized quote.'
    },
    {
      question: 'Is multi-company or Studio available in the One App Free plan?',
      answer:
        'No, multi-company management and Odoo Studio are advanced features only available in the Custom plan. These tools are designed for businesses that need to manage multiple entities or require extensive customization capabilities.'
    },
    {
      question: 'Why do I have multiple apps with the One App Free plan?',
      answer:
        "The One App Free plan includes one fully functional app plus several complementary apps that work together. For example, if you choose the CRM app, you'll also get access to related apps like Calendar, Contacts, and Discussions to ensure a complete experience."
    },
    {
      question: 'How to upgrade from the One App Free plan to a Standard or Custom plan?',
      answer:
        "You can upgrade at any time directly from your account settings. Simply go to your subscription page, choose your new plan, and complete the payment. Your data and configurations will be preserved, and you'll immediately gain access to all additional apps and features."
    },
    {
      question: 'What is the difference between the standard plan and the custom plan?',
      answer:
        'The Standard plan includes all apps and is hosted on Odoo Online (cloud). The Custom plan includes everything in Standard plus the ability to use on-premise hosting, Odoo.sh, Odoo Studio for customization, multi-company management, and external API access for integrations.'
    },
    {
      question: 'How do you define a paying user?',
      answer:
        'A paying user is anyone who needs to create, edit, or modify data in the system. Users who only need to view information (portal users) or external users accessing specific features (like customers viewing their orders) are typically free.'
    },
    {
      question:
        'Can I switch from a hosted plan (Odoo Online) to Odoo Enterprise or the other way around?',
      answer:
        'Yes, you can migrate between hosting options. However, this process requires planning and may involve some downtime. Contact our support team to discuss your migration needs and we\'ll help you plan a smooth transition.'
    },
    {
      question: 'What does External API mean?',
      answer:
        'External API access allows you to integrate Odoo with other software systems using programmatic interfaces. This is useful for connecting Odoo with third-party services, building custom applications, or automating workflows between different platforms. This feature is only available in the Custom plan.'
    }
  ];

  const toggleFAQ = (index) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <div className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Section Title */}
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
            Any Questions?
          </h2>
          <p className="text-muted-foreground text-lg">
            If the answer to your question is not on this page, please contact
            our Account Managers
          </p>
        </div>

        {/* FAQ Items */}
        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className="bg-card border border-border rounded-xl overflow-hidden hover:border-primary/40 transition-all duration-300"
            >
              <button
                onClick={() => toggleFAQ(index)}
                className="w-full flex items-center justify-between p-6 text-left"
              >
                <span className="text-foreground font-semibold text-lg pr-4">
                  {faq.question}
                </span>
                {openIndex === index ? (
                  <ChevronUp
                    size={24}
                    className="text-primary flex-shrink-0"
                  />
                ) : (
                  <ChevronDown
                    size={24}
                    className="text-muted-foreground flex-shrink-0"
                  />
                )}
              </button>

              {openIndex === index && (
                <div className="px-6 pb-6">
                  <div className="pt-4 border-t border-border">
                    <p className="text-muted-foreground leading-relaxed">{faq.answer}</p>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Contact CTA */}
        <div className="mt-12 text-center">
          <button className="px-8 py-4 bg-primary text-primary-foreground font-semibold rounded-xl hover:bg-primary/90 shadow-lg shadow-primary/30 transition-all duration-300">
            Contact Our Team
          </button>
        </div>
      </div>
    </div>
  );
};

export default FAQ;
