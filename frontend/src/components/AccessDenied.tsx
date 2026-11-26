import { Link } from 'react-router-dom'
import { buttonOutline } from './ui'

export default function AccessDenied() {
  return (
    <section className="py-20 text-center">
      <p className="font-display text-6xl font-semibold text-gold">403</p>
      <p className="mt-4 text-muted">Цей розділ доступний лише адміністраторам</p>
      <Link to="/" className={`${buttonOutline} mt-8`}>
        На головну
      </Link>
    </section>
  )
}
