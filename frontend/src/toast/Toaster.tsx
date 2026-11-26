import { useSyncExternalStore } from 'react'
import { dismissToast, getToasts, subscribeToasts, type Toast } from './store'

const toneClass: Record<Toast['tone'], string> = {
  success: 'border-emerald-500/40 text-emerald-200',
  error: 'border-danger/50 text-danger',
}

const iconPath: Record<Toast['tone'], string> = {
  success: 'M5 12.5l4.5 4.5L19 7.5',
  error: 'M12 7v6m0 4h.01',
}

function ToastItem({ toast }: { toast: Toast }) {
  return (
    <div
      role={toast.tone === 'error' ? 'alert' : 'status'}
      className={`pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-xl border bg-surface-raised px-4 py-3 text-sm shadow-xl ${toneClass[toast.tone]}`}
    >
      <svg viewBox="0 0 24 24" aria-hidden="true" className="mt-0.5 size-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d={iconPath[toast.tone]} />
      </svg>
      <p className="flex-1 text-zinc-100">{toast.text}</p>
      <button
        type="button"
        aria-label="Закрити повідомлення"
        className="-m-1 rounded p-1 text-muted hover:text-zinc-100"
        onClick={() => dismissToast(toast.id)}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true" className="size-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M6 6l12 12M18 6L6 18" />
        </svg>
      </button>
    </div>
  )
}

export default function Toaster() {
  const toasts = useSyncExternalStore(subscribeToasts, getToasts)

  return (
    <section
      aria-label="Повідомлення"
      className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex flex-col items-center gap-2 px-4 sm:inset-x-auto sm:right-4 sm:items-end"
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} />
      ))}
    </section>
  )
}
