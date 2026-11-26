import { useSimilarTitles } from '../../recommendations/queries'
import Shelf from '../shelf/Shelf'
import ShelfCard from '../shelf/ShelfCard'
import ShelfContent from '../shelf/ShelfContent'

export default function SimilarTitles({ titleId }: { titleId: number }) {
  const query = useSimilarTitles(titleId)

  return (
    <Shelf heading="Схожі">
      <ShelfContent
        state={query}
        items={query.data}
        emptyText="Схожих тайтлів у каталозі поки немає"
        itemKey={(item) => item.id}
        renderItem={(item) => <ShelfCard title={item} />}
      />
    </Shelf>
  )
}
