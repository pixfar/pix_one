import { createBrowserRouter } from "react-router-dom";
import Layout from "../layout/Layout";
import Home from "../pages/Home/Home";

export const router = createBrowserRouter([
    {
        element: <Layout />,
        path: '/',
        children: [
            {
                element: <Home />,
                path: '/'
            }
        ]
    }
])