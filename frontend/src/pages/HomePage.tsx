import { useAuth } from '../auth/useAuth'
import ContinueWatchingRow from '../components/history/ContinueWatchingRow'
import GuestHero from '../components/home/GuestHero'
import PopularRow from '../components/home/PopularRow'
import RecommendedRow from '../components/home/RecommendedRow'
import { useDocumentTitle } from '../hooks/useDocumentTitle'

function PersonalRows() {
  return (
    <>
      <h1 className="sr-only">Головна</h1>
      <ContinueWatchingRow />
      <RecommendedRow />
    </>
  )
}

export default function HomePage() {
  useDocumentTitle(null)
  const { status } = useAuth()

  return (
    <div className="space-y-12">
      {status === 'authenticated' && <PersonalRows />}
      {status === 'guest' && <GuestHero />}
      <PopularRow />
    </div>
  )
}
