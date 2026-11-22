import { useId, type TextareaHTMLAttributes } from 'react'
import { controlClass, labelClass } from './ui'

interface TextAreaFieldProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string
  error?: string
}

export default function TextAreaField({ label, error, ...textareaProps }: TextAreaFieldProps) {
  const id = useId()

  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className={labelClass}>
        {label}
      </label>
      <textarea
        id={id}
        rows={5}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : undefined}
        className={`${controlClass(Boolean(error))} resize-y`}
        {...textareaProps}
      />
      {error && (
        <p id={`${id}-error`} className="text-xs text-danger">
          {error}
        </p>
      )}
    </div>
  )
}
