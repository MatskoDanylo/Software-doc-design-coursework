import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'
import { ApiError } from './api/client'
import AuthProvider from './auth/AuthProvider'
import AppRoutes from './routes/AppRoutes'

const MAX_RETRIES = 1

function shouldRetry(failureCount: number, error: Error): boolean {
  const clientError = error instanceof ApiError && error.status >= 400 && error.status < 500
  return !clientError && failureCount < MAX_RETRIES
}

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: shouldRetry, refetchOnWindowFocus: false },
    },
  })
}

export default function App() {
  const [queryClient] = useState(createQueryClient)

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </QueryClientProvider>
  )
}
