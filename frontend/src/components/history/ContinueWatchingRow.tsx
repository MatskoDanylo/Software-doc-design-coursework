import { useQuery } from '@tanstack/react-query'
import { historyApi, historyKeys } from '../../api/history'
import { useAuth } from '../../auth/useAuth'
import Shelf from '../shelf/Shelf'
import ShelfContent from '../shelf/ShelfContent'
import ContinueCard from './ContinueCard'

export default function ContinueWatchingRow() {
  const { status } = useAuth()
  const query = useQuery({
    queryKey: historyKeys.all,
    queryFn: historyApi.continueWatching,
    enabled: status === 'authenticated',
  })

  if (status !== 'authenticated' || query.data?.length === 0) return null

  return (
    <Shelf heading="Продовжити перегляд">
      <ShelfContent
        state={query}
        items={query.data}
        itemKey={(entry) => entry.title.id}
        renderItem={(entry) => <ContinueCard entry={entry} />}
      />
    </Shelf>
  )
}
