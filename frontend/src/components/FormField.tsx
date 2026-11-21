import { useId, type InputHTMLAttributes } from 'react'

interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
  hint?: string
}

export default function FormField({ label, error, hint, ...inputProps }: FormFieldProps) {
  const id = useId()
  const messageId = `${id}-message`
  const message = error ?? hint
  const stateClass = error ? 'border-danger focus:ring-danger/40' : 'border-line focus:border-gold focus:ring-gold/30'

  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="block text-sm font-medium text-zinc-300">
        {label}
      </label>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={message ? messageId : undefined}
        className={`w-full rounded-lg border bg-screen px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:ring-2 focus:outline-none ${stateClass}`}
        {...inputProps}
      />
      {message && (
        <p id={messageId} className={`text-xs ${error ? 'text-danger' : 'text-muted'}`}>
          {message}
        </p>
      )}
    </div>
  )
}
