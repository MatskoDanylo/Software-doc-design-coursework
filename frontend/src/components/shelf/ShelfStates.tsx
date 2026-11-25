import { buttonOutline, buttonSmall } from '../ui'

const SKELETON_CARDS = 6

export function ShelfSkeleton() {
  return (
    <div role="status" className="flex gap-4 overflow-hidden pb-2">
      <span className="sr-only">Завантаження…</span>
      {Array.from({ length: SKELETON_CARDS }, (_, index) => (
        <div key={index} className="w-36 shrink-0 animate-pulse">
          <div className="aspect-[2/3] rounded-xl bg-surface-raised" />
          <div className="mt-2 h-4 w-3/4 rounded bg-surface-raised" />
          <div className="mt-2 h-3 w-1/2 rounded bg-surface-raised" />
        </div>
      ))}
    </div>
  )
}

export function ShelfError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div role="alert" className="flex flex-wrap items-center gap-3 rounded-xl border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger">
      <span>Не вдалося завантажити: {message}</span>
      <button type="button" className={`${buttonOutline} ${buttonSmall}`} onClick={onRetry}>
        Спробувати ще раз
      </button>
    </div>
  )
}

export function ShelfEmpty({ text }: { text: string }) {
  return <p className="rounded-xl border border-dashed border-line px-4 py-8 text-center text-sm text-muted">{text}</p>
}
