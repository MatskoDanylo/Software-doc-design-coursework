import { useState } from 'react'
import { buttonDanger, buttonGhost, buttonSmall } from '../ui'

interface ConfirmButtonProps {
  label: string
  question: string
  pending?: boolean
  confirmLabel?: string
  pendingLabel?: string
  dismissLabel?: string
  onConfirm: () => void
}

export default function ConfirmButton({
  label,
  question,
  pending = false,
  confirmLabel = 'Так, видалити',
  pendingLabel = 'Видалення…',
  dismissLabel = 'Скасувати',
  onConfirm,
}: ConfirmButtonProps) {
  const [asking, setAsking] = useState(false)

  if (!asking) {
    return (
      <button type="button" className={`${buttonDanger} ${buttonSmall}`} onClick={() => setAsking(true)}>
        {label}
      </button>
    )
  }

  return (
    <span role="group" aria-label={question} className="inline-flex flex-wrap items-center gap-2">
      <span className="text-xs text-zinc-300">{question}</span>
      <button type="button" className={`${buttonDanger} ${buttonSmall}`} disabled={pending} onClick={onConfirm}>
        {pending ? pendingLabel : confirmLabel}
      </button>
      <button type="button" className={`${buttonGhost} ${buttonSmall}`} disabled={pending} onClick={() => setAsking(false)}>
        {dismissLabel}
      </button>
    </span>
  )
}
