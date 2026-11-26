import type { ReactNode } from 'react'

interface ChartCardProps {
  title: string
  action?: ReactNode
  children: ReactNode
}

export default function ChartCard({ title, action, children }: ChartCardProps) {
  return (
    <figure className="rounded-2xl border border-line bg-surface p-4 sm:p-5">
      <figcaption className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <span className="text-sm font-medium text-zinc-200">{title}</span>
        {action}
      </figcaption>
      {children}
    </figure>
  )
}
