import type { ReactNode } from 'react'

interface FormAlertProps {
  tone?: 'error' | 'success'
  children: ReactNode
}

const toneClass = {
  error: 'border-danger/40 bg-danger/10 text-danger',
  success: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300',
}

export default function FormAlert({ tone = 'error', children }: FormAlertProps) {
  return (
    <div role={tone === 'error' ? 'alert' : 'status'} className={`rounded-lg border px-3 py-2 text-sm ${toneClass[tone]}`}>
      {children}
    </div>
  )
}
