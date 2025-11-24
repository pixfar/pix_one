import ServiceCard from "./ServiceCard/ServiceCard";
import { CircleDollarSign, ClipboardList, Settings, Star, Truck, Users } from 'lucide-react';

const servicesData = [
    {
        id: 1,
        icon: Settings,
        title: "Cloud ERP applications",
        description: "Say hello to future-ready using complete, modular solutions driven by built-in AI and analytics.",
        linkText: "Explore cloud ERP applications",
        linkHref: "#",
    },
    {
        id: 2,
        icon: CircleDollarSign ,
        title: "Financial management",
        description:
            "See what's coming and act with precision using solutions that help you manage uncertainty, optimise processes, and enable compliance.",
        linkText: "Explore financial management software",
        linkHref: "#",
    },
    {
        id: 3,
        icon: ClipboardList,
        title: "Spend management",
        description:
            "Implement AI-powered spend management processes from source to pay with an integrated suite of solutions to deliver spend visibility, control, and savings.",
        linkText: "Explore spend management solutions",
        linkHref: "#",
    },
    {
        id: 4,
        icon: Truck,
        title: "Supply chain management",
        description:
            "Run a risk-resilient and sustainable supply chain that can adapt to anything with our solutions for supply chain planning, manufacturing, and logistics.",
        linkText: "Explore supply chain solutions",
        linkHref: "#",
    },
    {
        id: 5,
        icon: Users,
        title: "Human capital management",
        description:
            "Align your workforce and business priorities with AI-enabled solutions for core HR and payroll, employee experience, talent management, and contingent workforce management functions.",
        linkText: "Explore HCM software",
        linkHref: "#",
    },
    {
        id: 6,
        icon: Star,
        title: "Customer experience",
        description:
            "Connect e-commerce, marketing, sales, and service data with our customer experience solutions—and use AI to personalise the customer experience at every touchpoint.",
        linkText: "Explore CRM and CX solutions",
        linkHref: "#",
    },
]
const Services = () => {
    return (
        <section className="w-full bg-background text-foreground">
            <div className="max-w-[1344px] mx-auto py-16 md:py-[100px] px-4 md:px-6">
                {/* Header Section */}
                <div className="mb-12">
                    <h2 className="text-2xl md:text-4xl font-bold  mb-4">Support every team and strengthen every process</h2>
                    <p className="text-muted-foreground">
                        Equip every team with the tools to adapt, scale, and deliver real results.
                    </p>
                </div>

                {/* Services Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {servicesData.map((service) => (
                        <ServiceCard
                            key={service.id}
                            icon={service.icon}
                            title={service.title}
                            description={service.description}
                            linkText={service.linkText}
                            linkHref={service.linkHref}
                        />
                    ))}
                </div>
            </div>
        </section>
    );
};

export default Services;