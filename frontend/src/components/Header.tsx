import { Link, NavLink } from 'react-router-dom'
import Avatar from './Avatar'
import Logo from './Logo'
import { buttonGhost, buttonOutline, buttonPrimary } from './ui'

export interface HeaderUser {
  displayName: string
  avatarUrl: string | null
  isAdmin: boolean
}

interface HeaderProps {
  user: HeaderUser | null
  pending: boolean
  onLogout: () => void
}

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `text-sm transition-colors ${isActive ? 'text-gold' : 'text-muted hover:text-zinc-100'}`

function UserMenu({ user, onLogout }: { user: HeaderUser; onLogout: () => void }) {
  return (
    <div className="flex items-center gap-3">
      <Link to="/profile" className="flex items-center gap-2 rounded-lg px-2 py-1 hover:bg-surface-raised">
        <Avatar name={user.displayName} url={user.avatarUrl} />
        <span className="max-w-40 truncate text-sm text-zinc-200">{user.displayName}</span>
      </Link>
      <button type="button" onClick={onLogout} className={buttonOutline}>
        Вихід
      </button>
    </div>
  )
}

function GuestActions() {
  return (
    <div className="flex items-center gap-2">
      <Link to="/login" className={buttonGhost}>
        Вхід
      </Link>
      <Link to="/register" className={buttonPrimary}>
        Реєстрація
      </Link>
    </div>
  )
}

export default function Header({ user, pending, onLogout }: HeaderProps) {
  return (
    <header className="sticky top-0 z-10 border-b border-line bg-screen/85 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-6 px-4">
        <div className="flex items-center gap-8">
          <Logo />
          <nav className="hidden items-center gap-6 sm:flex">
            <NavLink to="/" end className={navLinkClass}>
              Головна
            </NavLink>
            {user?.isAdmin && (
              <NavLink to="/admin" className={navLinkClass}>
                Адмінка
              </NavLink>
            )}
          </nav>
        </div>
        {!pending && (user ? <UserMenu user={user} onLogout={onLogout} /> : <GuestActions />)}
      </div>
    </header>
  )
}
