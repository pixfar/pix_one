
const Vission = () => {
    return (
        <div className="min-h-screen text-white bg-[#0a0a14]">
            <div className="max-w-[1344px] mx-auto  px-4 md:px-6 py-16 md:py-[100px]">
                {/* Main heading */}
                <h1 className="text-2xl md:text-4xl font-bold mb-12 max-w-3xl leading-tight">
                    Act with confidence now—lead with vision tomorrow
                </h1>

                {/* Content container */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center max-w-6xl mx-auto">
                    {/* Left side - Stacked cards */}
                    <div className="relative space-y-4">
                        {/* Connecting vertical line + arrow */}
                        <div className="absolute left-[27.5px] top-0 bottom-4 w-[2px] bg-blue-500  -translate-x-1/2 rounded-full">
                            {/* Arrow tip */}
                            <div className="absolute bottom-[-8px] left-1/2 -translate-x-1/2 w-0 h-0 border-l-[6px] border-r-[6px] border-t-[8px] border-l-transparent border-r-transparent border-t-blue-500"></div>
                        </div>

                        <div className="absolute right-[25.5px] top-0 bottom-4 w-[2px] bg-blue-500 -translate-x-1/2 rounded-full">
                            {/* Arrow tip */}
                            <div className="absolute bottom-[-7px] left-1/2 -translate-x-1/2 w-0 h-0 
                                            border-l-[6px] border-r-[6px] border-b-[8px] 
                                            border-l-transparent border-r-transparent border-b-blue-500">
                            </div>
                        </div>

                        {/* SAP Business AI Card */}
                        <div className="bg-purple-200 p-6 rounded-lg relative overflow-hidden">
                            {/* SVG Background */}
                            <div className="absolute inset-0 opacity-20">
                                <svg className="w-full h-full" viewBox="0 0 400 100" preserveAspectRatio="none">
                                    <defs>
                                        <pattern id="aiPattern" x="0" y="0" width="80" height="80" patternUnits="userSpaceOnUse">
                                            <path d="M0 40 L40 0 L80 40 L40 80 Z" stroke="#6B21A8" strokeWidth="1" fill="none" />
                                            <circle cx="40" cy="0" r="2" fill="#6B21A8" />
                                            <circle cx="0" cy="40" r="2" fill="#6B21A8" />
                                            <circle cx="80" cy="40" r="2" fill="#6B21A8" />
                                            <circle cx="40" cy="80" r="2" fill="#6B21A8" />
                                        </pattern>
                                    </defs>
                                    <rect width="400" height="100" fill="url(#aiPattern)" />
                                </svg>
                            </div>

                            <h3 className="text-xl font-bold text-black relative z-10 text-center">
                                SAP Business AI
                            </h3>
                        </div>



                        {/* SAP Business Data Cloud Card */}
                        <div className="bg-blue-500 p-6 rounded-lg relative overflow-hidden">
                            <div className="absolute inset-0 opacity-20">
                                <svg className="w-full h-full" viewBox="0 0 400 100" preserveAspectRatio="none">
                                    <defs>
                                        <pattern id="waves" x="0" y="0" width="60" height="60" patternUnits="userSpaceOnUse">
                                            <path d="M0,30 Q15,20 30,30 T60,30" stroke="white" strokeWidth="1" fill="none" />
                                        </pattern>
                                    </defs>
                                    <rect width="400" height="100" fill="url(#waves)" />
                                </svg>
                            </div>
                            <div className="flex items-center justify-center relative z-10">
                                <h3 className="text-xl font-bold text-black text-white">SAP Business Data Cloud</h3>
                            </div>
                        </div>

                        {/* SAP Business Applications Card */}
                        <div className="bg-blue-300 p-6 rounded-lg relative overflow-hidden">
                            <div className="absolute inset-0 opacity-15">
                                <svg className="w-full h-full" viewBox="0 0 400 100" preserveAspectRatio="none">
                                    <defs>
                                        <pattern id="icons" x="0" y="0" width="50" height="50" patternUnits="userSpaceOnUse">
                                            <rect x="10" y="10" width="30" height="30" fill="currentColor" />
                                        </pattern>
                                    </defs>
                                    <rect width="400" height="100" fill="url(#icons)" />
                                </svg>
                            </div>
                            <h3 className="text-xl font-bold text-black relative z-10 text-center">SAP Business Applications</h3>
                        </div>

                        {/* Bottom border with text */}
                        <div className="px-6 py-4 bg-white/10 rounded-b-lg  md:w-[90%] border-2 border-blue-500 border-t-0 md:mx-auto text-center">
                            <span className="text-sm font-medium">
                                powered by Pixfar ERP Solution Platform
                            </span>
                        </div>
                    </div>


                    {/* Right side - Content and buttons */}
                    <div className="space-y-6">
                        <div>
                            <h2 className="text-2xl font-bold mb-4">Built for what your business needs next</h2>
                            <p className="text-gray-300 leading-relaxed">
                                SAP Business Suite unites your AI, data, apps, and platform to help you adapt, innovate, and move
                                forward with clarity.
                            </p>
                        </div>

                        {/* button */}
                        <div className="flex flex-col gap-3">
                            <button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition-colors w-max">
                                Explore SAP Business Suite
                            </button>
                            <button className="border-2 border-blue-600 hover:bg-blue-500 hover:text-black font-semibold py-2 px-6 rounded-lg transition-colors w-max">
                                View SAP Business Suite packages
                            </button>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    );
};

export default Vission;