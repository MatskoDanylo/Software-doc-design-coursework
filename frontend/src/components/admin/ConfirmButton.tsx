import { useState } from 'react'
import { buttonDanger, buttonGhost, buttonSmall } from '../ui'

interface ConfirmButtonProps {
  label: string
  question: string
  pending?: boolean
  onConfirm: () => void
}

export default function ConfirmButton({ label, question, pending = false, onConfirm }: ConfirmButtonProps) {
  const [asking, setAsking] = useState(false)

  if (!asking) {
    return (
      <button type="button" className={`${buttonDanger} ${buttonSmall}`} onClick={() => setAsking(true)}>
        {label}
      </button>
    )
  }

  return (
    <span role="group" aria-label={question} className="inline-flex items-center gap-2">
      <span className="text-xs text-zinc-300">{question}</span>
      <button type="button" className={`${buttonDanger} ${buttonSmall}`} disabled={pending} onClick={onConfirm}>
        {pending ? 'Видалення…' : 'Так, видалити'}
      </button>
      <button type="button" className={`${buttonGhost} ${buttonSmall}`} disabled={pending} onClick={() => setAsking(false)}>
        Скасувати
      </button>
    </span>
  )
}
