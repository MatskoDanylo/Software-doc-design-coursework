import { useId, type ReactNode } from 'react'

interface ShelfProps {
  heading: string
  note?: ReactNode
  action?: ReactNode
  children: ReactNode
}

export default function Shelf({ heading, note, action, children }: ShelfProps) {
  const headingId = useId()

  return (
    <section aria-labelledby={headingId} className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-x-4 gap-y-2">
        <div>
          <h2 id={headingId} className="font-display text-2xl font-semibold">
            {heading}
          </h2>
          {note && <p className="mt-1 text-sm text-muted">{note}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  )
}
