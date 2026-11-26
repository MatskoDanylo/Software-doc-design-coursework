const bar = 'animate-pulse rounded bg-surface-raised'

export function TableSkeleton({ rows = 5, columns = 5 }: { rows?: number; columns?: number }) {
  return (
    <div role="status" className="space-y-3">
      <span className="sr-only">Завантаження…</span>
      <div className={`${bar} h-4 w-full opacity-60`} />
      {Array.from({ length: rows }, (_, row) => (
        <div key={row} className="flex gap-3">
          {Array.from({ length: columns }, (_, column) => (
            <div key={column} className={`${bar} h-8 ${column === 0 ? 'flex-[2]' : 'flex-1'}`} />
          ))}
        </div>
      ))}
    </div>
  )
}

export function ListSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div role="status" className="space-y-3">
      <span className="sr-only">Завантаження…</span>
      {Array.from({ length: rows }, (_, row) => (
        <div key={row} className={`${bar} h-9 w-full`} />
      ))}
    </div>
  )
}

export function TitleDetailsSkeleton() {
  return (
    <div role="status" className="grid gap-8 md:grid-cols-[18rem_1fr]">
      <span className="sr-only">Завантаження…</span>
      <div className={`${bar} aspect-[2/3] w-full max-w-72 rounded-xl`} />
      <div className="space-y-4">
        <div className={`${bar} h-4 w-40`} />
        <div className={`${bar} h-10 w-3/4`} />
        <div className={`${bar} h-6 w-24`} />
        <div className="space-y-2 pt-2">
          <div className={`${bar} h-4 w-full max-w-prose`} />
          <div className={`${bar} h-4 w-11/12 max-w-prose`} />
          <div className={`${bar} h-4 w-2/3 max-w-prose`} />
        </div>
        <div className={`${bar} h-10 w-48`} />
      </div>
    </div>
  )
}
