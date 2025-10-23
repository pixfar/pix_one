import Hyperspeed from "../../../components/Hyperspeed/Hyperspeed";

const Banner = () => {
    return (
        <div className="min-h-screen relative flex items-center justify-center overflow-hidden">
            {/* Background Animation */}
            <Hyperspeed />

            {/* Text Content */}
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-4 md:max-w-4xl md:mx-auto w-full md:-top-28">
                <h1 className="text-4xl md:text-6xl font-bold leading-tight md:leading-[80px] text-white drop-shadow-lg">
                    Empower Your Business with Intelligent ERP Solutions
                </h1>
                <div className="mt-8 flex items-center gap-5">
                    <button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-10 py-3  rounded-full  transition-all duration-300">
                        Get Started
                    </button>
                    <button className="bg-transparent border border-white hover:bg-white hover:text-blue-600 text-white font-semibold px-10 py-3 rounded-full  transition-all duration-300">
                        Learn More
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Banner;
