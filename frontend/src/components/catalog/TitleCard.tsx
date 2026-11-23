import { Link } from 'react-router-dom'
import type { Title } from '../../types/catalog'
import FavoriteButton from '../favorites/FavoriteButton'
import Poster from './Poster'
import RatingBadge from './RatingBadge'

const MAX_GENRES = 3

export default function TitleCard({ title }: { title: Title }) {
  const genres = title.genres.slice(0, MAX_GENRES).map((genre) => genre.name)

  return (
    <article className="relative">
      <Link
        to={`/titles/${title.id}`}
        className="group block rounded-xl focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-gold"
      >
        <div className="relative transition-transform group-hover:-translate-y-1">
          <Poster id={title.id} name={title.name} url={title.poster_url} />
          <RatingBadge rating={title.rating} className="absolute top-2 left-2" />
          {title.kind === 'series' && (
            <span className="absolute bottom-2 left-2 rounded-md bg-screen/80 px-2 py-0.5 text-xs text-zinc-200">Серіал</span>
          )}
        </div>
        <h3 className="mt-3 line-clamp-2 font-medium text-zinc-100 group-hover:text-gold">{title.name}</h3>
      </Link>
      <FavoriteButton title={title} className="absolute top-2 right-2" />
      <p className="mt-1 text-xs text-muted">
        {title.year}
        {genres.length > 0 && ` · ${genres.join(', ')}`}
      </p>
    </article>
  )
}
