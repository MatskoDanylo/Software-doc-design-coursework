import { useRef, type KeyboardEvent } from 'react'
import { REPORT_PANEL_ID, REPORT_TABS, reportTabId, type ReportTabId } from '../../../reports/filters'

const tabClass = (active: boolean) =>
  `rounded-lg px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-gold ${
    active ? 'bg-surface-raised text-gold' : 'text-muted hover:text-zinc-100'
  }`

export default function ReportTabs({ active, onSelect }: { active: ReportTabId; onSelect: (id: ReportTabId) => void }) {
  const listRef = useRef<HTMLDivElement>(null)

  const handleKeyDown = (event: KeyboardEvent) => {
    if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return
    const index = REPORT_TABS.findIndex((tab) => tab.id === active)
    const step = event.key === 'ArrowRight' ? 1 : -1
    const next = REPORT_TABS[(index + step + REPORT_TABS.length) % REPORT_TABS.length]
    onSelect(next.id)
    listRef.current?.querySelector<HTMLButtonElement>(`#${reportTabId(next.id)}`)?.focus()
  }

  return (
    <div ref={listRef} role="tablist" aria-label="Звіти" className="flex flex-wrap gap-2" onKeyDown={handleKeyDown}>
      {REPORT_TABS.map((tab) => (
        <button
          key={tab.id}
          id={reportTabId(tab.id)}
          type="button"
          role="tab"
          aria-selected={tab.id === active}
          aria-controls={REPORT_PANEL_ID}
          tabIndex={tab.id === active ? 0 : -1}
          className={tabClass(tab.id === active)}
          onClick={() => onSelect(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}
