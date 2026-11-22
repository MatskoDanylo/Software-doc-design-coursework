import { Link } from 'react-router-dom'
import { buttonPrimary } from '../components/ui'

export default function HomePage() {
  return (
    <section className="rounded-2xl border border-line bg-gradient-to-br from-surface to-screen px-8 py-20 text-center">
      <h1 className="font-display text-4xl font-semibold">Онлайн-кінотеатр</h1>
      <p className="mx-auto mt-4 max-w-xl text-muted">
        Фільми та серіали в різній якості. Шукайте за назвою, жанром, роком і країною.
      </p>
      <Link to="/catalog" className={`${buttonPrimary} mt-8`}>
        Перейти до каталогу
      </Link>
    </section>
  )
}
