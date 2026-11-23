import { Link } from 'react-router-dom'
import { watchPath } from '../../player/episodes'
import type { Season } from '../../types/catalog'

interface EpisodePanelProps {
  titleId: number
  seasons: Season[]
  currentId: number
}

function episodeClass(current: boolean): string {
  const state = current ? 'bg-gold/15 text-gold' : 'text-zinc-300 hover:bg-surface-raised hover:text-zinc-100'
  return `flex gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${state}`
}

export default function EpisodePanel({ titleId, seasons, currentId }: EpisodePanelProps) {
  return (
    <nav aria-label="Епізоди" className="space-y-4 rounded-xl border border-line bg-surface p-3 lg:max-h-[32rem] lg:overflow-y-auto">
      {seasons.map((season) => (
        <section key={season.id} aria-label={`Сезон ${season.number}`}>
          <h2 className="px-3 pb-1 text-xs font-semibold tracking-wide text-muted uppercase">Сезон {season.number}</h2>
          <ol>
            {season.episodes.map((episode) => (
              <li key={episode.id}>
                <Link
                  to={watchPath(titleId, episode.id)}
                  aria-label={`Епізод ${episode.number}: ${episode.name}`}
                  aria-current={episode.id === currentId ? 'true' : undefined}
                  className={episodeClass(episode.id === currentId)}
                >
                  <span className="w-6 shrink-0 text-muted">{episode.number}</span>
                  <span className="truncate">{episode.name}</span>
                </Link>
              </li>
            ))}
          </ol>
        </section>
      ))}
    </nav>
  )
}
