import { useRecommendationFeed } from '../../recommendations/queries'
import { POPULARITY, strategyLabel } from '../../recommendations/strategies'
import Shelf from '../shelf/Shelf'
import ShelfCard from '../shelf/ShelfCard'
import ShelfContent from '../shelf/ShelfContent'

function feedNote(strategy: string): string {
  if (strategy === POPULARITY) return 'Поки що це популярне. Подивіться щось або додайте у Вибране, і добірка стане персональною'
  return `Алгоритм: ${strategyLabel(strategy)}`
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
