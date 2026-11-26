import { Link } from 'react-router-dom'
import { watchPath } from '../../player/episodes'
import { formatClock, progressPercent } from '../../player/time'
import type { HistoryEntry } from '../../types/history'
import Poster from '../catalog/Poster'

function ProgressBar({ percent }: { percent: number }) {
  return (
    <div
      role="progressbar"
      aria-label="Переглянуто"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={percent}
      className="h-1 overflow-hidden rounded-full bg-line"
    >
      <div className="h-full bg-gold" style={{ width: `${percent}%` }} />
    </div>
  )
}

export default function ContinueCard({ entry }: { entry: HistoryEntry }) {
  const { title, episode, progress_sec, duration_sec } = entry
  const percent = progressPercent(progress_sec, duration_sec)
  const position = duration_sec ? `${formatClock(progress_sec)} з ${formatClock(duration_sec)}` : formatClock(progress_sec)

  return (
    <Link
      to={watchPath(title.id, episode?.id ?? null)}
      className="group block w-36 shrink-0 rounded-xl focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-gold"
    >
      <Poster id={title.id} name={title.name} url={title.poster_url} />
      <div className="mt-2 space-y-1.5">
        {percent !== null && <ProgressBar percent={percent} />}
        <p className="line-clamp-1 text-sm font-medium text-zinc-100 group-hover:text-gold">{title.name}</p>
        {episode && (
          <p className="line-clamp-1 text-xs text-muted">
            С{episode.season_number} Е{episode.number} · {episode.name}
          </p>
        )}
        <p className="text-xs text-muted">Зупинились на {position}</p>
      </div>
    </Link>
  )
}
