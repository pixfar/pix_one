import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/button';
import { useAuth } from '../../context/AuthContext';
import { ROUTES } from '../../config/routes.constants';
import { useTheme } from '../../context/ThemeProvider';
import { Moon, Sun } from 'lucide-react';

const Navbar = () => {
    const [isSticky, setIsSticky] = useState(false);
    const navigate = useNavigate();
    const { isAuthenticated, user, logout } = useAuth();
    const { resolvedTheme, setTheme } = useTheme();

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
            <div className="max-w-[1280px] mx-auto py-4">
                <div
                    className={`flex items-center justify-between px-8 py-3 border rounded-full backdrop-blur-md transition-all duration-500
                        ${isSticky ? "bg-background/80 border-border shadow-lg" : "bg-background/5 border-border"
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
                                <circle cx="16" cy="16" r="3" className="fill-foreground" />
                                <ellipse
                                    cx="16"
                                    cy="16"
                                    rx="12"
                                    ry="5"
                                    className="stroke-foreground"
                                    strokeWidth="2"
                                    fill="none"
                                />
                                <ellipse
                                    cx="16"
                                    cy="16"
                                    rx="12"
                                    ry="5"
                                    className="stroke-foreground"
                                    strokeWidth="2"
                                    fill="none"
                                    transform="rotate(60 16 16)"
                                />
                                <ellipse
                                    cx="16"
                                    cy="16"
                                    rx="12"
                                    ry="5"
                                    className="stroke-foreground"
                                    strokeWidth="2"
                                    fill="none"
                                    transform="rotate(120 16 16)"
                                />
                            </svg>
                        </div>
                        <span className="text-foreground text-xl font-medium">PixOne</span>
                    </div>

                    {/* Links */}
                    <div className="flex items-center gap-8">
                        {[
                            { label: "Home", href: "/pixone" },
                            { label: "Industries", href: "#" },
                            { label: "All Apps", href: "#" },
                            { label: "Pricing", href: "/pixone/pricing" },
                            { label: "Learning", href: "#" },
                            { label: "Help", href: "#" },
                            { label: "About Us", href: "#" }
                        ].map((item) => (
                            <a
                                key={item.label}
                                href={item.href}
                                className="text-foreground text-base font-medium hover:text-muted-foreground transition-colors"
                            >
                                {item.label}
                            </a>
                        ))}
                    </div>
                    <div className="flex items-center gap-4">
                        {/* Theme Toggle Button */}
                        <Button
                            variant="ghost"
                            size="icon"
                            className="w-9 h-9 rounded-full bg-transparent text-foreground border border-border hover:bg-accent transition-colors"
                            onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
                        >
                            {resolvedTheme === 'dark' ? (
                                <Sun className="h-4 w-4" />
                            ) : (
                                <Moon className="h-4 w-4" />
                            )}
                            <span className="sr-only">Toggle theme</span>
                        </Button>

                        {isAuthenticated ? (
                            <>
                                <Button
                                    variant="outline"
                                    className="px-4 py-2 text-sm font-medium"
                                    onClick={() => navigate(ROUTES.DASHBOARD)}
                                >
                                    Dashboard
                                </Button>
                                <Button
                                    variant="outline"
                                    className="px-4 py-2 text-sm font-medium"
                                    onClick={async () => {
                                        await logout();
                                        navigate(ROUTES.HOME);
                                    }}
                                >
                                    Logout
                                </Button>
                            </>
                        ) : (
                            <>
                                <Button
                                    variant="outline"
                                    className="px-4 py-2 text-sm font-medium"
                                    onClick={() => navigate(ROUTES.SIGN_IN)}
                                >
                                    Sign In
                                </Button>
                                <Button
                                    variant="default"
                                    className="px-4 py-2 text-sm font-medium"
                                    onClick={() => window.open("https://demo.pixfar.com", "_blank")}
                                >
                                    Try it Now
                                </Button>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
