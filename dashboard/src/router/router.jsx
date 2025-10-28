import { createBrowserRouter } from "react-router-dom";
import Layout from "../layout/Layout";
import Home from "../pages/Home/Home";
import Dashboard from "@/pages/Dashboard/Dashboard";

export const router = createBrowserRouter([
    {
        element: <Layout />,
        path: '/',
        children: [
            {
                element: <Home />,
                path: '/'
            },

        ]
    },

    // dashboard
    {
        element: <Dashboard />,
        path: '/my-dashboard/profile'
    }
])