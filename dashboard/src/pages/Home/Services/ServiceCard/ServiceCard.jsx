const ServiceCard = ({ icon: Icon, title, description, linkText, linkHref }) => {
    return (
        <div className="flex flex-col items-start bg-white/5 border border-white/10 hover:border-blue-500/40 rounded-2xl p-6 shadow-md hover:shadow-blue-500/20 transition-all duration-300 cursor-pointer group">

            {/* Icon Container */}
            <div className="p-3 bg-blue-500/10 rounded-xl mb-4 group-hover:bg-blue-500/20 transition-colors duration-300">
                <Icon size={40} className="text-blue-400 group-hover:text-blue-500 transition-colors duration-300" />
            </div>

            {/* Title */}
            <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-blue-400 transition-colors">
                {title}
            </h3>

            {/* Description */}
            <p className="text-sm text-gray-400 leading-relaxed mb-5">
                {description}
            </p>

            {/* Link */}
            <a
                href={linkHref}
                className="text-blue-400 text-sm font-medium hover:text-blue-300 transition-all inline-flex items-center gap-1"
            >
                {linkText}
                <span className="translate-x-0 group-hover:translate-x-1 transition-transform">›</span>
            </a>
        </div>
    );
};

export default ServiceCard;
