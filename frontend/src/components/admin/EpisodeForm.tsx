import { useState, type FormEvent } from 'react'
import { errorMessage } from '../../api/errors'
import { EPISODE_MAX, nameError, numberError } from '../../admin/catalogForms'
import type { EpisodePayload } from '../../types/adminCatalog'
import { buttonGhost, buttonOutline, buttonSmall, controlClass } from '../ui'

interface EpisodeFormProps {
  initial: EpisodePayload
  submitLabel: string
  pending: boolean
  error: unknown
  onSubmit: (payload: EpisodePayload) => void
  onCancel?: () => void
}

export default function EpisodeForm({ initial, submitLabel, pending, error, onSubmit, onCancel }: EpisodeFormProps) {
  const [number, setNumber] = useState(String(initial.number))
  const [name, setName] = useState(initial.name)
  const [clientError, setClientError] = useState<string>()
  const message = clientError ?? (error ? errorMessage(error) : undefined)

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const validation = numberError(number, EPISODE_MAX) ?? nameError(name)
    setClientError(validation)
    if (!validation) onSubmit({ number: Number(number), name: name.trim() })
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="space-y-1">
      <div className="flex flex-wrap items-center gap-2">
        <input
          aria-label="Номер епізоду"
          type="number"
          min={1}
          max={EPISODE_MAX}
          value={number}
          className={`${controlClass(Boolean(message))} w-20 py-1.5`}
          onChange={(event) => setNumber(event.target.value)}
        />
        <input
          aria-label="Назва епізоду"
          value={name}
          maxLength={255}
          placeholder="Назва епізоду"
          className={`${controlClass(Boolean(message))} min-w-48 flex-1 py-1.5`}
          onChange={(event) => setName(event.target.value)}
        />
        <button type="submit" disabled={pending} className={`${buttonOutline} ${buttonSmall}`}>
          {pending ? 'Збереження…' : submitLabel}
        </button>
        {onCancel && (
          <button type="button" disabled={pending} className={`${buttonGhost} ${buttonSmall}`} onClick={onCancel}>
            Скасувати
          </button>
        )}
      </div>
      {message && (
        <p role="alert" className="text-xs text-danger">
          {message}
        </p>
      )}
    </form>
  )
}
