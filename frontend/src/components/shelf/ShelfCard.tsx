import { Link } from 'react-router-dom'
import type { Title } from '../../types/catalog'
import Poster from '../catalog/Poster'
import RatingBadge from '../catalog/RatingBadge'
import FavoriteButton from '../favorites/FavoriteButton'

const MAX_GENRES = 2

function defaultCaption(title: Title): string {
  return [String(title.year), ...title.genres.slice(0, MAX_GENRES).map((genre) => genre.name)].join(' · ')
}

export default function ShelfCard({ title, reason }: { title: Title; reason?: string }) {
  return (
    <article className="relative w-36 shrink-0">
      <Link
        to={`/titles/${title.id}`}
        className="group block rounded-xl focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-gold"
      >
        <div className="relative">
          <Poster id={title.id} name={title.name} url={title.poster_url} />
          <RatingBadge rating={title.rating} className="absolute top-2 left-2" />
        </div>
        <h3 className="mt-2 line-clamp-1 text-sm font-medium text-zinc-100 group-hover:text-gold">{title.name}</h3>
      </Link>
      <FavoriteButton title={title} className="absolute top-2 right-2" />
      <p className={`mt-1 line-clamp-2 text-xs ${reason ? 'text-gold/80' : 'text-muted'}`}>{reason || defaultCaption(title)}</p>
    </article>
  )
}
