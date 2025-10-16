import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { FrappeProvider } from 'frappe-react-sdk'
import App from './App.jsx'
import { RouterProvider } from 'react-router-dom'
import { router } from './router/router.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <FrappeProvider url="http://localhost:5173">
      <RouterProvider router={router} />
    </FrappeProvider>
  </StrictMode>,
)
