import { useQuery } from '@tanstack/react-query'
import { useId } from 'react'
import { errorMessage } from '../../api/errors'
import { historyApi, historyKeys } from '../../api/history'
import { useAuth } from '../../auth/useAuth'
import ContinueCard from './ContinueCard'

export default function ContinueWatchingRow() {
  const headingId = useId()
  const { status } = useAuth()
  const query = useQuery({
    queryKey: historyKeys.all,
    queryFn: historyApi.continueWatching,
    enabled: status === 'authenticated',
  })

  if (status !== 'authenticated' || query.isPending) return null
  if (query.isError) {
    return <p className="text-sm text-danger">Не вдалося завантажити історію: {errorMessage(query.error)}</p>
  }
  if (query.data.length === 0) return null

  return (
    <section aria-labelledby={headingId} className="space-y-4">
      <h2 id={headingId} className="font-display text-2xl font-semibold">
        Продовжити перегляд
      </h2>
      <ol className="flex gap-4 overflow-x-auto pb-2">
        {query.data.map((entry) => (
          <li key={entry.title.id}>
            <ContinueCard entry={entry} />
          </li>
        ))}
      </ol>
    </section>
  )
}
