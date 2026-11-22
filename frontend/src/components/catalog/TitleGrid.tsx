import type { Title } from '../../types/catalog'
import TitleCard from './TitleCard'

const gridClass = 'grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 xl:grid-cols-4'

export default function TitleGrid({ titles, dimmed = false }: { titles: Title[]; dimmed?: boolean }) {
  return (
    <div className={`${gridClass} transition-opacity ${dimmed ? 'opacity-60' : ''}`} aria-busy={dimmed || undefined}>
      {titles.map((title) => (
        <TitleCard key={title.id} title={title} />
      ))}
    </div>
  )
}

export function TitleGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div role="status" className={gridClass}>
      <span className="sr-only">Завантаження…</span>
      {Array.from({ length: count }, (_, index) => (
        <div key={index} className="animate-pulse">
          <div className="aspect-[2/3] rounded-xl bg-surface-raised" />
          <div className="mt-3 h-4 w-3/4 rounded bg-surface-raised" />
          <div className="mt-2 h-3 w-1/2 rounded bg-surface-raised" />
        </div>
      ))}
    </div>
  )
}
