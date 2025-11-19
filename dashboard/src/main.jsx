import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '../src/styles/index.css'
import { FrappeProvider } from 'frappe-react-sdk'
import App from './App.jsx'
import { RouterProvider } from 'react-router-dom'
import { router } from './router/router.jsx'
import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'
import { ThemeProvider } from './context/ThemeProvider'
import { DirectionProvider } from './context/DirectionProvider'
import { LayoutProvider } from './context/LayoutProvider'

const queryClient = new QueryClient()

// url="http://localhost:5173"

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <FrappeProvider > 
      <QueryClientProvider client={queryClient}>
        <LayoutProvider>
          <ThemeProvider>
            <DirectionProvider>
              <RouterProvider router={router} />
            </DirectionProvider>
          </ThemeProvider>
        </LayoutProvider>
      </QueryClientProvider>
    </FrappeProvider>
  </StrictMode>,
)
