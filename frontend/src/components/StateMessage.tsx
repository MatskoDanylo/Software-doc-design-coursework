import type { ReactNode } from 'react'

interface StateMessageProps {
  title: string
  text?: string
  tone?: 'neutral' | 'error'
  action?: ReactNode
}

export default function StateMessage({ title, text, tone = 'neutral', action }: StateMessageProps) {
  return (
    <div
      role={tone === 'error' ? 'alert' : 'status'}
      className="rounded-2xl border border-dashed border-line px-6 py-16 text-center"
    >
      <p className={`font-display text-xl font-semibold ${tone === 'error' ? 'text-danger' : 'text-zinc-100'}`}>{title}</p>
      {text && <p className="mt-2 text-sm text-muted">{text}</p>}
      {action && <div className="mt-6 flex justify-center">{action}</div>}
    </div>
  )
}
