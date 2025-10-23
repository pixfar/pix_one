export const serviceApps = [
    { icon: "accounting", label: "Qucik Books" },
    { icon: "knowledge", label: "Notion" },
    { icon: "sign", label: "Document Sign" },
    { icon: "crm", label: "Sales Force" },
    { icon: "studio", label: "Pwer Apps" },
    { icon: "subscriptions", label: "Chargebee" },
    { icon: "rental", label: "Rental" },
    { icon: "pointofsale", label: "Lightspeed" },
    { icon: "discuss", label: "Discuss" },
    { icon: "documents", label: "Slack" },
    { icon: "project", label: "Asana" },
    { icon: "timesheets", label: "Harvest" },
    { icon: "", label: "Service Cloud" },
    { icon: "", label: "Planing" },
    { icon: "", label: "Zendesk" },
    { icon: "", label: "Shopify" },
    { icon: "", label: "Social Marketing" },
    { icon: "", label: "Hubspot" },
    { icon: "", label: "SAP" },
    { icon: "", label: "BambooHR" },
    { icon: "", label: "Tableau" },
]

const ServiceTools = ({ icon, label }) => {

    const iconMap = {
        accounting: "📊",
        knowledge: "📚",
        sign: "✍️",
        crm: "🎯",
        studio: "🎨",
        subscriptions: "🔄",
        rental: "🔑",
        pointofsale: "💳",
        discuss: "💬",
        documents: "📄",
        project: "✅",
        timesheets: "⏱️",
    }
    return (
        <div className="flex flex-col items-center text-center gap-3 group cursor-pointer">
            {/* Icon container */}
            <div className="relative flex items-center justify-center w-16 h-16 rounded-lg bg-gradient-to-br from-blue-500/20 to-blue-400/10 group-hover:from-blue-500/30 group-hover:to-blue-400/20 transition-all duration-500 shadow-md group-hover:shadow-blue-500/20">
                <div className="absolute inset-0 rounded-lg border border-blue-400/30 group-hover:border-blue-400/50 transition-colors duration-500"></div>
                <span className="text-blue-400 text-3xl group-hover:text-blue-300 transition-all duration-500 transform group-hover:scale-110">
                    {iconMap[icon] || "📦"}
                </span>
            </div>

            {/* Label */}
            <p className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors duration-300">
                {label}
            </p>
        </div>

    );
};

export default ServiceTools;