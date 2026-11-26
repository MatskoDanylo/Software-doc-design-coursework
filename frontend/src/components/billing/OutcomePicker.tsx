import { OUTCOMES } from '../../billing/outcomes'
import type { PaymentOutcome } from '../../types/billing'
import { labelClass } from '../ui'

interface OutcomePickerProps {
  value: PaymentOutcome
  onChange: (outcome: PaymentOutcome) => void
}

export default function OutcomePicker({ value, onChange }: OutcomePickerProps) {
  return (
    <fieldset>
      <legend className={labelClass}>Відповідь банку</legend>
      <div className="mt-3 space-y-3">
        {OUTCOMES.map((option) => {
          const selected = option.value === value
          return (
            <label
              key={option.value}
              className={`flex cursor-pointer gap-3 rounded-lg border p-3 transition-colors ${
                selected ? 'border-gold bg-gold/5' : 'border-line hover:border-zinc-500'
              }`}
            >
              <input
                type="radio"
                name="outcome"
                value={option.value}
                checked={selected}
                onChange={() => onChange(option.value)}
                aria-labelledby={`outcome-${option.value}`}
                aria-describedby={`outcome-${option.value}-hint`}
                className="mt-1 accent-gold"
              />
              <span>
                <span id={`outcome-${option.value}`} className="block font-medium text-zinc-100">
                  {option.label}
                </span>
                <span id={`outcome-${option.value}-hint`} className="block text-sm text-muted">
                  {option.description}
                </span>
              </span>
            </label>
          )
        })}
      </div>
    </fieldset>
  )
}
