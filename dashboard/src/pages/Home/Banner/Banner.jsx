import Hyperspeed from "../../../components/Hyperspeed/Hyperspeed";

const Banner = () => {
    return (
        <div className="min-h-screen relative flex items-center justify-center overflow-hidden">
            {/* Background Animation */}
            <Hyperspeed />

            {/* Text Content */}
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-4 md:max-w-4xl md:mx-auto w-full md:-top-28">
                <h1 className="text-4xl md:text-6xl font-bold leading-tight md:leading-[80px] text-foreground drop-shadow-lg">
                    Empower Your Business with Intelligent ERP Solutions
                </h1>
                <div className="mt-8 flex items-center gap-5">
                    <a href="https://demo.pixfar.com" target="_blank" rel="noopener noreferrer" className="bg-primary hover:bg-primary/90 text-primary-foreground font-semibold px-10 py-3  rounded-full  transition-all duration-300">
                        Get Free Tier
                    </a>
                    <button className="bg-transparent border border-border hover:bg-accent hover:text-accent-foreground text-foreground font-semibold px-10 py-3 rounded-full  transition-all duration-300">
                        Learn More
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Banner;
