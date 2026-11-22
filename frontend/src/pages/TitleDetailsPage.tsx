import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { catalogApi, catalogKeys } from '../api/catalog'
import { ApiError } from '../api/client'
import { errorMessage } from '../api/errors'
import Poster from '../components/catalog/Poster'
import RatingBadge from '../components/catalog/RatingBadge'
import SeasonList from '../components/catalog/SeasonList'
import PageLoader from '../components/PageLoader'
import StateMessage from '../components/StateMessage'
import { buttonOutline, buttonPrimary, chipClass } from '../components/ui'
import type { TitleDetail } from '../types/catalog'

const KIND_LABEL = { movie: 'Фільм', series: 'Серіал' } as const

function BackLink() {
  return (
    <Link to="/catalog" className={buttonOutline}>
      До каталогу
    </Link>
  )
}

function TitleInfo({ title }: { title: TitleDetail }) {
  return (
    <div className="min-w-0 space-y-5">
      <div>
        <p className="text-sm text-muted">
          {KIND_LABEL[title.kind]} · {title.year} · {title.country}
        </p>
        <h1 className="mt-1 font-display text-4xl font-semibold">{title.name}</h1>
      </div>
      <RatingBadge rating={title.rating} className="text-sm" />
      {title.genres.length > 0 && (
        <ul className="flex flex-wrap gap-2" aria-label="Жанри">
          {title.genres.map((genre) => (
            <li key={genre.id}>
              <Link to={`/catalog?genre=${genre.id}`} className={chipClass(false)}>
                {genre.name}
              </Link>
            </li>
          ))}
        </ul>
      )}
      <p className="max-w-prose leading-relaxed text-zinc-300">{title.description || 'Опис відсутній'}</p>
      <div className="flex flex-wrap items-center gap-3">
        <button type="button" className={buttonPrimary} disabled aria-describedby="watch-hint">
          ▶ Дивитись
        </button>
        <span id="watch-hint" className="text-xs text-muted">
          Перегляд стане доступним найближчим часом
        </span>
      </div>
    </div>
  )
}

export default function TitleDetailsPage() {
  const id = Number(useParams().id)
  const valid = Number.isInteger(id) && id > 0
  const query = useQuery({ queryKey: catalogKeys.title(id), queryFn: () => catalogApi.title(id), enabled: valid })

  if (!valid || (query.error instanceof ApiError && query.error.status === 404)) {
    return <StateMessage title="Тайтл не знайдено" text="Можливо, його видалили з каталогу" action={<BackLink />} />
  }
  if (query.isError) {
    return <StateMessage tone="error" title="Не вдалося завантажити сторінку" text={errorMessage(query.error)} action={<BackLink />} />
  }
  if (query.isPending) return <PageLoader />

  const title = query.data
  return (
    <article className="space-y-12">
      <div className="grid gap-8 md:grid-cols-[18rem_1fr]">
        <Poster id={title.id} name={title.name} url={title.poster_url} className="w-full max-w-72" />
        <TitleInfo title={title} />
      </div>
      {title.kind === 'series' && (
        <section aria-labelledby="seasons-heading" className="space-y-4">
          <h2 id="seasons-heading" className="font-display text-2xl font-semibold">
            Сезони та епізоди
          </h2>
          <SeasonList seasons={title.seasons} />
        </section>
      )}
    </article>
  )
}
