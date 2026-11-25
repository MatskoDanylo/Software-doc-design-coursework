export default function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-line bg-surface px-4 py-3">
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="mt-1 font-display text-2xl font-semibold text-zinc-100 tabular-nums">{value}</dd>
    </div>
  )
}

export function StatTileSkeleton() {
  return (
    <div className="animate-pulse rounded-xl border border-line bg-surface px-4 py-3">
      <div className="h-3 w-2/3 rounded bg-surface-raised" />
      <div className="mt-2 h-7 w-1/2 rounded bg-surface-raised" />
    </div>
  )
}
