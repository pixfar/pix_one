
const Footer = () => {
    return (
        <footer className="bg-background border-t border-border">
            <div className="max-w-[1280px] mx-auto px-4  mt-10 pt-20 pb-10">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                    {/* Column 1: Logo and Description */}
                    <div>
                        <h3 className="text-foreground text-2xl font-bold mb-4">Pixfar</h3>
                        <p className="text-muted-foreground text-sm leading-relaxed">
                            Building innovative solutions for the modern web. Empowering developers with cutting-edge tools and
                            technologies.
                        </p>
                    </div>

                    {/* Column 2: Services */}
                    <div>
                        <h4 className="text-foreground text-lg font-semibold mb-4">Services</h4>
                        <ul className="space-y-2">
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground transition-colors text-sm">
                                    Web Development
                                </a>
                            </li>
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground transition-colors text-sm">
                                    UI/UX Design
                                </a>
                            </li>
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground transition-colors text-sm">
                                    Consulting
                                </a>
                            </li>
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground transition-colors text-sm">
                                    Support
                                </a>
                            </li>
                        </ul>
                    </div>

                    {/* Column 3: Links */}
                    <div>
                        <h4 className="text-foreground text-lg font-semibold mb-4">Links</h4>
                        <ul className="space-y-2">
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground transition-colors text-sm">
                                    About Us
                                </a>
                            </li>
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground transition-colors text-sm">
                                    Blog
                                </a>
                            </li>
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground transition-colors text-sm">
                                    Careers
                                </a>
                            </li>
                            <li>
                                <a href="#" className="text-muted-foreground hover:text-foreground transition-colors text-sm">
                                    Contact
                                </a>
                            </li>
                        </ul>
                    </div>

                    {/* Column 4: Newsletter */}
                    <div>
                        <h4 className="text-foreground text-lg font-semibold mb-4">Newsletter</h4>
                        <p className="text-muted-foreground text-sm mb-4">Subscribe to get the latest updates and news.</p>
                        <form className="flex flex-col gap-2">
                            <input
                                type="email"
                                placeholder="Enter your email"
                                className="px-4 py-2 bg-card border border-border rounded-lg text-foreground text-sm placeholder:text-muted-foreground focus:outline-none focus:border-primary transition-colors"
                            />
                            <button
                                type="submit"
                                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                            >
                                Subscribe
                            </button>
                        </form>
                    </div>
                </div>

                {/* Copyright */}
                <div className="mt-12 pt-8 border-t border-border">
                    <p className="text-muted-foreground text-sm text-center">© {new Date().getFullYear()} Pixfar. All rights reserved.</p>
                </div>
            </div>
        </footer>
    );
};

export default Footer;