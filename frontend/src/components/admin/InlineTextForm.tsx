import { useState, type FormEvent } from 'react'
import { errorMessage } from '../../api/errors'
import { buttonGhost, buttonOutline, buttonSmall, controlClass } from '../ui'

interface InlineTextFormProps {
  label: string
  submitLabel: string
  initial?: string
  type?: 'text' | 'number'
  maxLength?: number
  pending: boolean
  error: unknown
  validate: (value: string) => string | undefined
  onSubmit: (value: string) => void
  onCancel?: () => void
}

export default function InlineTextForm({
  label,
  submitLabel,
  initial = '',
  type = 'text',
  maxLength,
  pending,
  error,
  validate,
  onSubmit,
  onCancel,
}: InlineTextFormProps) {
  const [value, setValue] = useState(initial)
  const [clientError, setClientError] = useState<string>()
  const message = clientError ?? (error ? errorMessage(error) : undefined)

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const validation = validate(value)
    setClientError(validation)
    if (!validation) onSubmit(value.trim())
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="space-y-1">
      <div className="flex flex-wrap items-center gap-2">
        <input
          aria-label={label}
          type={type}
          value={value}
          maxLength={maxLength}
          aria-invalid={message ? true : undefined}
          className={`${controlClass(Boolean(message))} ${type === 'number' ? 'w-24' : 'min-w-48 flex-1'} py-1.5`}
          onChange={(event) => {
            setValue(event.target.value)
            setClientError(undefined)
          }}
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
