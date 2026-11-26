import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import PageLoader from '../components/PageLoader'
import { redirectPath } from './redirect'

export default function GuestRoute() {
  const { status } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <PageLoader />
  if (status === 'authenticated') return <Navigate to={redirectPath(location.state)} replace />
  return <Outlet />
}
