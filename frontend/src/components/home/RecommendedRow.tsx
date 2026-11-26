import { useRecommendationFeed } from '../../recommendations/queries'
import { POPULARITY, strategyLabel } from '../../recommendations/strategies'
import Shelf from '../shelf/Shelf'
import ShelfCard from '../shelf/ShelfCard'
import ShelfContent from '../shelf/ShelfContent'

function feedNote(strategy: string): string {
  const note = `Алгоритм: ${strategyLabel(strategy)}`
  if (strategy !== POPULARITY) return note
  return `${note}. Якщо ви ще нічого не дивились, переглядайте й додавайте у Вибране, щоб добірка стала персональною`
}

export default function RecommendedRow() {
  const query = useRecommendationFeed()

  return (
    <Shelf heading="Рекомендовано для вас" note={query.data && feedNote(query.data.strategy)}>
      <ShelfContent
        state={query}
        items={query.data?.items}
        emptyText="Ви вже переглянули все, що ми можемо порадити. Загляньте в каталог"
        itemKey={(item) => item.id}
        renderItem={(item) => <ShelfCard title={item} reason={item.reason} />}
      />
    </Shelf>
  )
}
