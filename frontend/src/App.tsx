import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'
import AppRoutes from './routes/AppRoutes'

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: 1, refetchOnWindowFocus: false },
    },
  })
}

export default function App() {
  const [queryClient] = useState(createQueryClient)

  return (
    <QueryClientProvider client={queryClient}>
      <AppRoutes />
    </QueryClientProvider>
  )
}
