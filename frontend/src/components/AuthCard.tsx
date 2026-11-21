import type { ReactNode } from 'react'
import { card } from './ui'

interface AuthCardProps {
  title: string
  subtitle: string
  footer: ReactNode
  children: ReactNode
}

export default function AuthCard({ title, subtitle, footer, children }: AuthCardProps) {
  return (
    <div className="mx-auto max-w-md">
      <div className={`${card} shadow-2xl shadow-black/40`}>
        <h1 className="font-display text-2xl font-semibold">{title}</h1>
        <p className="mt-1 text-sm text-muted">{subtitle}</p>
        <div className="mt-6">{children}</div>
      </div>
      <p className="mt-6 text-center text-sm text-muted">{footer}</p>
    </div>
  )
}
