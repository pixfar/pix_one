import { iconMap } from "../../../../data/ServiceData";


const ServiceTools = ({ icon, label }) => {
    const iconSrc = iconMap[icon];

    return (
        <div className="flex flex-col items-center text-center gap-3 group cursor-pointer">
            {/* Icon container */}
            <div className="relative flex items-center justify-center w-16 h-16 rounded-lg bg-gradient-to-br from-blue-500/20 to-blue-400/10 group-hover:from-blue-500/30 group-hover:to-blue-400/20 transition-all duration-500 shadow-md group-hover:shadow-blue-500/20">
                <div className="absolute inset-0 rounded-lg border border-blue-400/30 group-hover:border-blue-400/50 transition-colors duration-500"></div>

                {/* Icon Image */}
                {iconSrc ? (
                    <img
                        src={iconSrc}
                        alt={label}
                        className="w-8 h-8 object-contain transition-all duration-500 transform group-hover:scale-110"
                    />
                ) : (
                    <span className="text-blue-400 text-2xl group-hover:text-blue-300 transition-all duration-500 transform group-hover:scale-110">
                        📦
                    </span>
                )}
            </div>

            {/* Label */}
            <p className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors duration-300">
                {label}
            </p>
        </div>
    );
};

export default ServiceTools;