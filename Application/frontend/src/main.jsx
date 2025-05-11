import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import App from './App.jsx'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 1000 * 60, // 1 minute
      cacheTime: 1000 * 60 * 10, // 10 minutes
    },
  },
})

// Configure global query behaviors
queryClient.setQueryDefaults(['status'], {
  refetchInterval: 30000, // Poll every 30 seconds
  refetchIntervalInBackground: false, // Don't poll in background
})

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)
