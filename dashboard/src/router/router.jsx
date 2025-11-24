import { createBrowserRouter } from "react-router-dom";
import Layout from "../layout/Layout";
import Home from "../pages/Home/Home";
import Dashboard from "@/pages/Dashboard/Dashboard";
import Pricing from "@/pages/Pricing/Pricing";
import SignIn from "@/pages/Auth/SignIn";
import SignUp from "@/pages/Auth/SignUp";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import PublicRoute from "@/components/auth/PublicRoute";
import { ROUTES } from "@/config/routes.constants";

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
            }
        ]
    },

    // Auth routes (public only)
    {
        element: <PublicRoute><SignIn /></PublicRoute>,
        path: ROUTES.SIGN_IN
    },
    {
        element: <PublicRoute><SignUp /></PublicRoute>,
        path: ROUTES.SIGN_UP
    },

    // Protected dashboard routes
    {
        element: <ProtectedRoute><Dashboard /></ProtectedRoute>,
        path: ROUTES.DASHBOARD
    },
    {
        element: <ProtectedRoute><Dashboard /></ProtectedRoute>,
        path: ROUTES.PROFILE
    }
], {
    basename: '/pixone'
})