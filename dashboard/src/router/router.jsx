import { createBrowserRouter } from "react-router-dom";
import Layout from "../layout/Layout";
import Home from "../pages/Home/Home";
import Dashboard from "@/pages/Dashboard/Dashboard";
import Pricing from "@/pages/Pricing/Pricing";
import Profile from "@/pages/Profile/Profile";

export const router = createBrowserRouter([
    {
        element: <Layout />,
        path: '/',
        children: [
            {
                element: <Home />,
                path: '/'
            },
            {
                element: <Pricing />,
                path: '/pricing'
            },
            {
                element: <Profile />,
                path:'/profile'
            }

        ]
    },

    // dashboard
    {
        element: <Dashboard />,
        path: '/my-dashboard/profile'
    }
], {
    basename: '/pixone'
})