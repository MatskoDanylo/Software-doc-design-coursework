import type { Season } from '../../types/catalog'

export default function SeasonList({ seasons }: { seasons: Season[] }) {
  if (seasons.length === 0) return <p className="text-sm text-muted">Сезони ще не додані</p>

  return (
    <div className="space-y-3">
      {seasons.map((season, index) => (
        <details key={season.id} open={index === 0} className="group rounded-xl border border-line bg-surface">
          <summary className="flex cursor-pointer items-center justify-between px-4 py-3 font-medium select-none">
            <span>Сезон {season.number}</span>
            <span className="text-sm text-muted">{season.episodes.length} еп.</span>
          </summary>
          {season.episodes.length === 0 ? (
            <p className="border-t border-line px-4 py-3 text-sm text-muted">Епізодів поки немає</p>
          ) : (
            <ol className="divide-y divide-line border-t border-line">
              {season.episodes.map((episode) => (
                <li key={episode.id} className="flex gap-3 px-4 py-2.5 text-sm">
                  <span className="w-8 shrink-0 text-muted">{episode.number}</span>
                  <span className="text-zinc-200">{episode.name}</span>
                </li>
              ))}
            </ol>
          )}
        </details>
      ))}
    </div>
  )
}
