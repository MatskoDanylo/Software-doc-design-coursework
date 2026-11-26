import { useId } from 'react'
import { parseYear, YEAR_MAX, YEAR_MIN, yearRangeError } from '../../catalog/filters'
import { useDebouncedCallback } from '../../hooks/useDebouncedCallback'
import { useSyncedDraft } from '../../hooks/useSyncedDraft'
import { controlClass, labelClass } from '../ui'

export const YEAR_DEBOUNCE_MS = 500

interface YearRangeFilterProps {
  from: number | null
  to: number | null
  onChange: (from: number | null, to: number | null) => void
}

interface YearInputProps {
  label: string
  value: string
  errorId?: string
  onChange: (value: string) => void
}

function YearInput({ label, value, errorId, onChange }: YearInputProps) {
  return (
    <input
      type="number"
      inputMode="numeric"
      aria-label={`Рік ${label.toLowerCase()}`}
      placeholder={label}
      min={YEAR_MIN}
      max={YEAR_MAX}
      value={value}
      aria-invalid={errorId ? true : undefined}
      aria-describedby={errorId}
      className={controlClass(Boolean(errorId))}
      onChange={(event) => onChange(event.target.value)}
    />
  )
}

export default function YearRangeFilter({ from, to, onChange }: YearRangeFilterProps) {
  const id = useId()
  const [fromDraft, setFromDraft] = useSyncedDraft(from?.toString() ?? '')
  const [toDraft, setToDraft] = useSyncedDraft(to?.toString() ?? '')
  const error = yearRangeError(fromDraft, toDraft)
  const errorId = error ? `${id}-error` : undefined
  const commit = useDebouncedCallback((nextFrom: string, nextTo: string) => {
    if (!yearRangeError(nextFrom, nextTo)) onChange(parseYear(nextFrom), parseYear(nextTo))
  }, YEAR_DEBOUNCE_MS)

  return (
    <fieldset className="space-y-1.5">
      <legend className={labelClass}>Рік виходу</legend>
      <div className="grid grid-cols-2 gap-2">
        <YearInput
          label="Від"
          value={fromDraft}
          errorId={errorId}
          onChange={(value) => {
            setFromDraft(value)
            commit(value, toDraft)
          }}
        />
        <YearInput
          label="До"
          value={toDraft}
          errorId={errorId}
          onChange={(value) => {
            setToDraft(value)
            commit(fromDraft, value)
          }}
        />
      </div>
      {error && (
        <p id={errorId} className="text-xs text-danger">
          {error}
        </p>
      )}
    </fieldset>
  )
}
