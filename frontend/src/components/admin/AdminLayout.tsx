import { NavLink, Outlet } from 'react-router-dom'

const LINKS = [
  { to: '/admin', label: 'Огляд', end: true },
  { to: '/admin/titles', label: 'Фільми та серіали', end: false },
  { to: '/admin/genres', label: 'Жанри', end: false },
  { to: '/admin/payments', label: 'Платежі', end: false },
  { to: '/admin/users', label: 'Користувачі', end: false },
  { to: '/admin/reports', label: 'Звіти', end: false },
  { to: '/admin/settings', label: 'Налаштування', end: false },
]

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-lg px-3 py-1.5 text-sm transition-colors ${
    isActive ? 'bg-surface-raised text-gold' : 'text-muted hover:text-zinc-100'
  }`

export default function AdminLayout() {
  return (
    <div className="space-y-8">
      <nav aria-label="Розділи адмінки" className="flex flex-wrap gap-2 border-b border-line pb-4">
        {LINKS.map((link) => (
          <NavLink key={link.to} to={link.to} end={link.end} className={linkClass}>
            {link.label}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </div>
  )
}
