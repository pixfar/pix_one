import Navbar from '../components/Shared/Navbar';
import { Outlet } from 'react-router-dom'
import Footer from '../components/Shared/Footer';

const Layout = () => {
    return (
        <div className=' min-h-screen bg-[#0a0a14] text-white '>
            <Navbar />
            <div className=''>
                <Outlet />
            </div>
            <Footer />
        </div>
    );
};

export default Layout;