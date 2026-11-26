import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ApiError } from '../../api/client'
import { errorMessage } from '../../api/errors'
import { playbackApi, playbackKeys } from '../../api/playback'
import { useAuth } from '../../auth/useAuth'
import { firstEpisode, watchPath } from '../../player/episodes'
import type { TitleDetail } from '../../types/catalog'
import { buttonPrimary } from '../ui'

function DisabledWatch({ hint }: { hint: string }) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <button type="button" className={buttonPrimary} disabled aria-describedby="watch-hint">
        ▶ Дивитись
      </button>
      <span id="watch-hint" className="text-xs text-muted">
        {hint}
      </span>
    </div>
  )
}

function unavailableHint(error: Error): string {
  if (error instanceof ApiError && error.code === 'video_not_ready') return 'Відео ще не завантажено'
  return errorMessage(error)
}

function AvailabilityCheck({ title }: { title: TitleDetail }) {
  const episodeId = title.kind === 'series' ? (firstEpisode(title.seasons)?.id ?? null) : null
  const noEpisodes = title.kind === 'series' && episodeId === null
  const query = useQuery({
    queryKey: playbackKeys.detail(title.id, episodeId),
    queryFn: () => playbackApi.get(title.id, episodeId),
    enabled: !noEpisodes,
  })

  if (noEpisodes) return <DisabledWatch hint="Епізодів поки немає" />
  if (query.isPending) return <DisabledWatch hint="Перевіряємо наявність відео…" />
  if (query.isError) return <DisabledWatch hint={unavailableHint(query.error)} />
  return (
    <Link to={watchPath(title.id, episodeId)} className={buttonPrimary}>
      ▶ Дивитись
    </Link>
  )
}

export default function WatchButton({ title }: { title: TitleDetail }) {
  const { status } = useAuth()

  if (status === 'loading') return <DisabledWatch hint="Завантаження…" />
  if (status === 'guest') {
    return (
      <Link to={watchPath(title.id)} className={buttonPrimary}>
        ▶ Увійти, щоб дивитись
      </Link>
    )
  }
  return <AvailabilityCheck title={title} />
}
