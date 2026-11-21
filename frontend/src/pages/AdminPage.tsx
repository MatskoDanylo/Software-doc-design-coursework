import { card } from '../components/ui'

const sections = [
  { title: 'Каталог', text: 'Фільми, серіали, жанри' },
  { title: 'Відео', text: 'Завантаження і HLS-конвертація' },
  { title: 'Користувачі', text: 'Акаунти і підписки' },
  { title: 'Звіти', text: 'Популярність, активність, доходи' },
]

export default function AdminPage() {
  return (
    <div>
      <h1 className="font-display text-3xl font-semibold">Адмін-панель</h1>
      <p className="mt-2 text-muted">Розділи зʼявляться на наступних етапах</p>
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {sections.map((section) => (
          <div key={section.title} className={`${card} opacity-70`}>
            <h2 className="font-medium text-gold">{section.title}</h2>
            <p className="mt-2 text-sm text-muted">{section.text}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
