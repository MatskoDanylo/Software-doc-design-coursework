import { Link } from 'react-router-dom'
import { buttonGhost, buttonOutline, buttonPrimary } from '../ui'

export default function GuestHero() {
  return (
    <section className="rounded-2xl border border-line bg-gradient-to-br from-surface to-screen px-8 py-14 text-center">
      <h1 className="font-display text-4xl font-semibold">Онлайн-кінотеатр</h1>
      <p className="mx-auto mt-4 max-w-xl text-muted">
        Увійдіть, щоб отримувати рекомендації за вашими переглядами і продовжувати перегляд з того ж місця.
      </p>
      <div className="mt-8 flex flex-wrap justify-center gap-3">
        <Link to="/login" className={buttonPrimary}>
          Увійти
        </Link>
        <Link to="/register" className={buttonOutline}>
          Зареєструватися
        </Link>
        <Link to="/catalog" className={buttonGhost}>
          До каталогу
        </Link>
      </div>
    </section>
  )
}
