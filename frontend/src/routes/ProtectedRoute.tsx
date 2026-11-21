import { Outlet } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import PageLoader from '../components/PageLoader'
import RedirectToLogin from './RedirectToLogin'

export default function ProtectedRoute() {
  const { status } = useAuth()

  if (status === 'loading') return <PageLoader />
  if (status === 'guest') return <RedirectToLogin />
  return <Outlet />
}
