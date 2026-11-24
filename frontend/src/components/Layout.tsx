import { Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import Header, { type HeaderUser } from './Header'

const currentYear = new Date().getFullYear()

export default function Layout() {
  const { user, status, logout } = useAuth()
  const navigate = useNavigate()

  const headerUser: HeaderUser | null = user && {
    displayName: user.profile.display_name,
    avatarUrl: user.profile.avatar_url,
    isAdmin: user.role === 'admin',
    plan: user.subscription.plan_code,
  }

  const handleLogout = () => {
    logout()
    navigate('/', { replace: true })
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Header user={headerUser} pending={status === 'loading'} onLogout={handleLogout} />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10">
        <Outlet />
      </main>
      <footer className="border-t border-line py-6 text-center text-xs text-muted">
        Cinema Platform · {currentYear}
      </footer>
    </div>
  )
}
