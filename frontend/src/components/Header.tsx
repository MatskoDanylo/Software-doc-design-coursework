import { Link, NavLink } from 'react-router-dom'
import Logo from './Logo'
import { buttonGhost, buttonOutline, buttonPrimary } from './ui'

export interface HeaderUser {
  displayName: string
}

interface HeaderProps {
  user: HeaderUser | null
  onLogout: () => void
}

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `text-sm transition-colors ${isActive ? 'text-gold' : 'text-muted hover:text-zinc-100'}`

export default function Header({ user, onLogout }: HeaderProps) {
  return (
    <header className="sticky top-0 z-10 border-b border-line bg-screen/85 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-6 px-4">
        <div className="flex items-center gap-8">
          <Logo />
          <nav className="hidden items-center gap-6 sm:flex">
            <NavLink to="/" end className={navLinkClass}>
              Головна
            </NavLink>
          </nav>
        </div>
        {user ? (
          <div className="flex items-center gap-3">
            <span className="max-w-40 truncate text-sm text-zinc-300">{user.displayName}</span>
            <button type="button" onClick={onLogout} className={buttonOutline}>
              Вихід
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Link to="/login" className={buttonGhost}>
              Вхід
            </Link>
            <Link to="/register" className={buttonPrimary}>
              Реєстрація
            </Link>
          </div>
        )}
      </div>
    </header>
  )
}
