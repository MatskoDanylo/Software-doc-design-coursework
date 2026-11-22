import { buttonGhost, buttonOutline, buttonSmall } from './ui'

interface PaginationProps {
  page: number
  totalPages: number
  onChange: (page: number) => void
}

const WINDOW = 2

function pageNumbers(page: number, totalPages: number): (number | 'gap')[] {
  const pages = new Set([1, totalPages])
  for (let p = page - WINDOW; p <= page + WINDOW; p++) if (p >= 1 && p <= totalPages) pages.add(p)
  const sorted = [...pages].sort((a, b) => a - b)
  return sorted.flatMap((p, index) => (index > 0 && p - sorted[index - 1] > 1 ? ['gap' as const, p] : [p]))
}

export default function Pagination({ page, totalPages, onChange }: PaginationProps) {
  if (totalPages <= 1) return null

  return (
    <nav aria-label="Сторінки" className="flex flex-wrap items-center justify-center gap-1">
      <button type="button" className={`${buttonGhost} ${buttonSmall}`} disabled={page <= 1} onClick={() => onChange(page - 1)}>
        ← Назад
      </button>
      {pageNumbers(page, totalPages).map((item, index) =>
        item === 'gap' ? (
          <span key={`gap-${index}`} className="px-2 text-muted">
            …
          </span>
        ) : (
          <button
            key={item}
            type="button"
            aria-current={item === page ? 'page' : undefined}
            className={`${item === page ? buttonOutline : buttonGhost} ${buttonSmall} min-w-9`}
            onClick={() => onChange(item)}
          >
            {item}
          </button>
        ),
      )}
      <button
        type="button"
        className={`${buttonGhost} ${buttonSmall}`}
        disabled={page >= totalPages}
        onClick={() => onChange(page + 1)}
      >
        Далі →
      </button>
    </nav>
  )
}
