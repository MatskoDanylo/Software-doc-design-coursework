import { Link } from 'react-router-dom'
import { card } from '../../ui'

const SECTIONS = [
  { title: 'Фільми та серіали', text: 'Додавання, редагування, постери, сезони, епізоди й відео', to: '/admin/titles' },
  { title: 'Жанри', text: 'Довідник жанрів каталогу', to: '/admin/genres' },
  { title: 'Платежі', text: 'Історія оплат і підтвердження платежів, що очікують', to: '/admin/payments' },
  { title: 'Користувачі', text: 'Акаунти, видача і зняття Premium', to: '/admin/users' },
  { title: 'Звіти', text: 'Популярність, активність, доходи, експорт CSV', to: '/admin/reports' },
  { title: 'Налаштування', text: 'Стратегія рекомендацій, ваги гібриду, вікно популярності', to: '/admin/settings' },
]

export default function AdminSections() {
  return (
    <nav aria-label="Розділи" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {SECTIONS.map((section) => (
        <Link key={section.to} to={section.to} className={`${card} transition-colors hover:border-gold`}>
          <h2 className="font-medium text-gold">{section.title}</h2>
          <p className="mt-2 text-sm text-muted">{section.text}</p>
        </Link>
      ))}
    </nav>
  )
}
