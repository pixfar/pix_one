import ServiceTools, { serviceApps } from "./ServiceTools/ServiceTools";

const BusinessPlatform = () => {
    return (
        <div className="min-h-screen bg-[#0a0a14] text-white">
            {/* Hero Section */}
            <div className="py-16 px-4 sm:px-6 lg:px-8">
                <div className="max-w-4xl mx-auto text-center">
                    {/* Main Heading */}
                    <h1 className="text-4xl sm:text-5xl lg:text-6xl font-normal mb-4 leading-tight whitespace-nowrap">
                        All your business on{" "}
                        <span className="relative inline-block">
                            {/* Highlight background */}
                            <span
                                className="absolute inset-x-0 bottom-1 h-4 bg-[#FFB629] -rotate-2 rounded-sm"
                                style={{ zIndex: 0 }}
                            ></span>
                            {/* Foreground text */}
                            <span className="relative z-10  italic ">
                                one platform.
                            </span>
                        </span>
                    </h1>


                    {/* Subheading */}
                    <p className="text-xl sm:text-2xl font-normal  mb-8 leading-relaxed">
                        Simple, efficient, yet{" "}
                        <span className="relative inline-block">
                            {/* <span
                                className="absolute inset-x-0 bottom-0 left-8 h-2 bg-blue-500 rotate-0 rounded-sm"
                                style={{ zIndex: 0 }}
                            ></span> */}
                            <span className="relative ">US$ 2.25/month for ALL Apps</span>
                        </span>
                    </p>

                    {/* CTA Buttons and Pricing Note */}
                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12 relative">
                        <button className="px-6 py-3 bg-[#714B67] text-white font-medium rounded hover:bg-[#563d4f] transition-colors">
                            Start now - it's free
                        </button>
                        <button className="px-6 py-3 bg-[#F3F4F6] text-[#714B67] font-medium border border-gray-300 rounded hover:bg-gray-50 transition-colors">
                            Meet an advisor
                        </button>

                        
                    </div>
                </div>
            </div>

            {/* Apps Grid Section */}
            <div className="bg-black py-10 px-4 sm:px-6 lg:px-8 rounded-t-[50%]">
                <div className="max-w-4xl mx-auto">
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-6 py-24">
                        {serviceApps.map((app, index) => (
                            <div key={index} className="flex justify-center">
                                <ServiceTools icon={app.icon} label={app.label} />
                            </div>
                        ))}
                    </div>
                </div>
            </div>


        </div>
    );
};

export default BusinessPlatform;