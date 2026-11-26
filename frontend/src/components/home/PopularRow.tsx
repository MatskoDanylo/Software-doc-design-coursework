import { Link } from 'react-router-dom'
import { useRecommendationFeed } from '../../recommendations/queries'
import { POPULARITY } from '../../recommendations/strategies'
import Shelf from '../shelf/Shelf'
import ShelfCard from '../shelf/ShelfCard'
import ShelfContent from '../shelf/ShelfContent'
import { textLink } from '../ui'

export default function PopularRow() {
  const query = useRecommendationFeed(POPULARITY)
  const action = (
    <Link to="/catalog?sort=popularity" className={`${textLink} text-sm`}>
      Увесь каталог →
    </Link>
  )

  return (
    <Shelf heading="Популярне" action={action}>
      <ShelfContent
        state={query}
        items={query.data?.items}
        emptyText="У каталозі поки немає тайтлів"
        itemKey={(item) => item.id}
        renderItem={(item) => <ShelfCard title={item} />}
      />
    </Shelf>
  )
}
