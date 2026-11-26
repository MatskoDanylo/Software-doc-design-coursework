import { useQuery } from '@tanstack/react-query'
import { Link, Navigate, useParams, useSearchParams } from 'react-router-dom'
import { catalogApi, catalogKeys } from '../api/catalog'
import { ApiError } from '../api/client'
import { errorMessage } from '../api/errors'
import { playbackApi, playbackKeys } from '../api/playback'
import { useAuth } from '../auth/useAuth'
import EpisodePanel from '../components/player/EpisodePanel'
import PlanBadge from '../components/player/PlanBadge'
import PlaybackStage from '../components/player/PlaybackStage'
import PageLoader from '../components/PageLoader'
import StateMessage from '../components/StateMessage'
import { buttonOutline, textLink } from '../components/ui'
import { episodeLabel, firstEpisode, flattenEpisodes, nextEpisode, watchPath, type EpisodeRef } from '../player/episodes'
import RedirectToLogin from '../routes/RedirectToLogin'
import type { TitleDetail } from '../types/catalog'
import { useDocumentTitle } from '../hooks/useDocumentTitle'

function parseId(value: string | null): number | null {
  const id = Number(value)
  return value !== null && Number.isInteger(id) && id > 0 ? id : null
}

function BackLink({ to, label }: { to: string; label: string }) {
  return (
    <Link to={to} className={buttonOutline}>
      {label}
    </Link>
  )
}

function PlaybackArea({ title, episode }: { title: TitleDetail; episode: EpisodeRef | null }) {
  const { user } = useAuth()
  const episodeId = episode?.id ?? null
  const query = useQuery({
    queryKey: playbackKeys.detail(title.id, episodeId),
    queryFn: () => playbackApi.get(title.id, episodeId),
    refetchOnMount: 'always',
  })

  if (query.error instanceof ApiError && query.error.status === 401) return <RedirectToLogin />
  if (query.isError) {
    const notReady = query.error instanceof ApiError && query.error.code === 'video_not_ready'
    return (
      <StateMessage
        tone={notReady ? 'neutral' : 'error'}
        title={notReady ? 'Відео ще недоступне' : 'Не вдалося підготувати відтворення'}
        text={errorMessage(query.error)}
        action={<BackLink to={`/titles/${title.id}`} label="До опису" />}
      />
    )
  }
  if (!query.isFetchedAfterMount || !query.data) return <PageLoader />

  return (
    <div className="space-y-4">
      <PlanBadge plan={user?.subscription.plan_code ?? query.data.plan} />
      <PlaybackStage
        key={episodeId ?? 'movie'}
        playback={query.data}
        target={{ titleId: title.id, episodeId }}
        next={episode ? nextEpisode(title.seasons, episode.id) : null}
      />
    </div>
  )
}

function WatchView({ title, episode }: { title: TitleDetail; episode: EpisodeRef | null }) {
  return (
    <section className="space-y-6">
      <header>
        <Link to={`/titles/${title.id}`} className={`${textLink} text-sm`}>
          ← {title.name}
        </Link>
        <h1 className="mt-2 font-display text-3xl font-semibold">{title.name}</h1>
        {episode && <p className="mt-1 text-muted">{episodeLabel(episode)}</p>}
      </header>
      <div className={episode ? 'grid gap-6 lg:grid-cols-[1fr_18rem]' : ''}>
        <PlaybackArea title={title} episode={episode} />
        {episode && <EpisodePanel titleId={title.id} seasons={title.seasons} currentId={episode.id} />}
      </div>
    </section>
  )
}

export default function WatchPage() {
  const titleId = Number(useParams().titleId)
  const [params] = useSearchParams()
  const episodeId = parseId(params.get('episode'))
  const valid = Number.isInteger(titleId) && titleId > 0
  const query = useQuery({ queryKey: catalogKeys.title(titleId), queryFn: () => catalogApi.title(titleId), enabled: valid })
  useDocumentTitle(query.data ? `${query.data.name} — перегляд` : 'Перегляд')
  const catalogLink = <BackLink to="/catalog" label="До каталогу" />

  if (!valid || (query.error instanceof ApiError && query.error.status === 404)) {
    return <StateMessage title="Тайтл не знайдено" text="Можливо, його видалили з каталогу" action={catalogLink} />
  }
  if (query.isError) {
    return <StateMessage tone="error" title="Не вдалося завантажити тайтл" text={errorMessage(query.error)} action={catalogLink} />
  }
  if (query.isPending) return <PageLoader />

  const title = query.data
  if (title.kind === 'movie') return <WatchView title={title} episode={null} />

  if (episodeId === null) {
    const first = firstEpisode(title.seasons)
    if (!first) return <StateMessage title="Епізодів поки немає" action={<BackLink to={`/titles/${title.id}`} label="До опису" />} />
    return <Navigate to={watchPath(title.id, first.id)} replace />
  }
  const episode = flattenEpisodes(title.seasons).find((item) => item.id === episodeId)
  if (!episode) {
    return <StateMessage title="Епізод не знайдено" action={<BackLink to={watchPath(title.id)} label="До першого епізоду" />} />
  }
  return <WatchView title={title} episode={episode} />
}
