import { Link } from 'react-router-dom'
import { buttonOutline } from '../components/ui'
import { useDocumentTitle } from '../hooks/useDocumentTitle'

export default function NotFoundPage() {
  useDocumentTitle('Сторінку не знайдено')
  return (
    <section className="py-20 text-center">
      <p className="font-display text-6xl font-semibold text-gold">404</p>
      <p className="mt-4 text-muted">Сторінку не знайдено</p>
      <Link to="/" className={`${buttonOutline} mt-8`}>
        На головну
      </Link>
    </section>
  )
}
