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

// Payment callback pages
import PaymentSuccess from "@/pages/Payment/PaymentSuccess";
import PaymentFailed from "@/pages/Payment/PaymentFailed";
import PaymentCancelled from "@/pages/Payment/PaymentCancelled";

// Subscription pages
import MySubscriptions from "@/pages/Dashboard/Subscriptions/MySubscriptions";
import SubscriptionDetails from "@/pages/Dashboard/Subscriptions/SubscriptionDetails";

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
    },

    // Payment callback routes (protected)
    {
        element: <ProtectedRoute><PaymentSuccess /></ProtectedRoute>,
        path: ROUTES.PAYMENT_SUCCESS
    },
    {
        element: <ProtectedRoute><PaymentFailed /></ProtectedRoute>,
        path: ROUTES.PAYMENT_FAILED
    },
    {
        element: <ProtectedRoute><PaymentCancelled /></ProtectedRoute>,
        path: ROUTES.PAYMENT_CANCELLED
    },

    // Subscription routes (protected)
    {
        element: <ProtectedRoute><MySubscriptions /></ProtectedRoute>,
        path: ROUTES.SUBSCRIPTIONS
    },
    {
        element: <ProtectedRoute><SubscriptionDetails /></ProtectedRoute>,
        path: ROUTES.SUBSCRIPTION_DETAILS
    }
], {
    basename: '/pixone'
})