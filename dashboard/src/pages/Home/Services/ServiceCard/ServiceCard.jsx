const ServiceCard = ({ icon: Icon, title, description, linkText, linkHref }) => {
    return (
        <div className="flex flex-col items-start bg-card border border-border hover:border-primary/40 rounded-2xl p-6 shadow-md hover:shadow-primary/20 transition-all duration-300 cursor-pointer group">

            {/* Icon Container */}
            <div className="p-3 bg-primary/10 rounded-xl mb-4 group-hover:bg-primary/20 transition-colors duration-300">
                <Icon size={40} className="text-primary group-hover:text-primary/80 transition-colors duration-300" />
            </div>

            {/* Title */}
            <h3 className="text-lg font-semibold text-foreground mb-2 group-hover:text-primary transition-colors">
                {title}
            </h3>

            {/* Description */}
            <p className="text-sm text-muted-foreground leading-relaxed mb-5">
                {description}
            </p>

            {/* Link */}
            <a
                href={linkHref}
                className="text-primary text-sm font-medium hover:text-primary/80 transition-all inline-flex items-center gap-1"
            >
                {linkText}
                <span className="translate-x-0 group-hover:translate-x-1 transition-transform">›</span>
            </a>
        </div>
    );
};

export default ServiceCard;
