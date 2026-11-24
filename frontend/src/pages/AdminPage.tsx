import { Link } from 'react-router-dom'
import { card } from '../components/ui'

const sections = [
  { title: 'Фільми та серіали', text: 'Додавання, редагування, постери, сезони й епізоди', to: '/admin/titles' },
  { title: 'Жанри', text: 'Довідник жанрів каталогу', to: '/admin/genres' },
  { title: 'Відео', text: 'Завантаження і HLS-конвертація' },
  { title: 'Платежі', text: 'Історія оплат і підтвердження платежів, що очікують', to: '/admin/payments' },
  { title: 'Користувачі', text: 'Акаунти, видача і зняття Premium', to: '/admin/users' },
  { title: 'Звіти', text: 'Популярність, активність, доходи' },
]

export default function AdminPage() {
  return (
    <div>
      <h1 className="font-display text-3xl font-semibold">Адмін-панель</h1>
      <p className="mt-2 text-muted">Оберіть розділ</p>
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {sections.map((section) =>
          section.to ? (
            <Link key={section.title} to={section.to} className={`${card} transition-colors hover:border-gold`}>
              <h2 className="font-medium text-gold">{section.title}</h2>
              <p className="mt-2 text-sm text-muted">{section.text}</p>
            </Link>
          ) : (
            <div key={section.title} className={`${card} opacity-60`}>
              <h2 className="font-medium text-zinc-300">{section.title}</h2>
              <p className="mt-2 text-sm text-muted">{section.text}</p>
              <p className="mt-3 text-xs text-muted">Зʼявиться згодом</p>
            </div>
          ),
        )}
      </div>
    </div>
  )
}
