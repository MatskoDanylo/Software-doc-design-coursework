import { Outlet } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import AccessDenied from '../components/AccessDenied'
import PageLoader from '../components/PageLoader'
import RedirectToLogin from './RedirectToLogin'

export default function AdminRoute() {
  const { status, user } = useAuth()

  if (status === 'loading') return <PageLoader />
  if (!user) return <RedirectToLogin />
  if (user.role !== 'admin') return <AccessDenied />
  return <Outlet />
}
