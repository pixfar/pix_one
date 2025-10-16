import { useState, useEffect } from 'react';

const Navbar = () => {
    const [isSticky, setIsSticky] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            if (window.scrollY > 100) {
                setIsSticky(true);
            } else {
                setIsSticky(false);
            }
        };

        window.addEventListener("scroll", handleScroll);
        return () => window.removeEventListener("scroll", handleScroll);
    }, []);

    return (
        <nav
            className={`w-full sticky left-0 z-50 transition-all  duration-500 ease-in-out ${isSticky
                    ? "top-0 translate-y-0 "
                    : "top-[-80px] bg-transparent translate-y-6"
                }`}
        >
            <div className="max-w-3xl mx-auto px-6 py-4">
                <div
                    className={`flex items-center justify-between px-8 py-3 border border-white/10 rounded-full transition-all duration-500 ${isSticky ? "bg-white/10" : "bg-white/5"
                        }`}
                >
                    {/* Logo */}
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 relative">
                            <svg
                                viewBox="0 0 32 32"
                                fill="none"
                                xmlns="http://www.w3.org/2000/svg"
                                className="w-full h-full"
                            >
                                <circle cx="16" cy="16" r="3" fill="white" />
                                <ellipse
                                    cx="16"
                                    cy="16"
                                    rx="12"
                                    ry="5"
                                    stroke="white"
                                    strokeWidth="2"
                                    fill="none"
                                />
                                <ellipse
                                    cx="16"
                                    cy="16"
                                    rx="12"
                                    ry="5"
                                    stroke="white"
                                    strokeWidth="2"
                                    fill="none"
                                    transform="rotate(60 16 16)"
                                />
                                <ellipse
                                    cx="16"
                                    cy="16"
                                    rx="12"
                                    ry="5"
                                    stroke="white"
                                    strokeWidth="2"
                                    fill="none"
                                    transform="rotate(120 16 16)"
                                />
                            </svg>
                        </div>
                        <span className="text-white text-xl font-medium">Pixfar ERP</span>
                    </div>

                    {/* Links */}
                    <div className="flex items-center gap-8">
                        {["Home", "Service", "Package"].map((item) => (
                            <a
                                key={item}
                                href="#"
                                className="text-white text-base font-medium hover:text-gray-300 transition-colors"
                            >
                                {item}
                            </a>
                        ))}
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
