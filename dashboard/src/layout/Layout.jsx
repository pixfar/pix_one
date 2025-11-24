import Navbar from '../components/Shared/Navbar';
import { Outlet } from 'react-router-dom'
import Footer from '../components/Shared/Footer';

const Layout = () => {
    return (
        <div className='min-h-screen bg-background text-foreground'>
            <Navbar />
            <div className=''>
                <Outlet />
            </div>
            <Footer />
        </div>
    );
};

export default Layout;