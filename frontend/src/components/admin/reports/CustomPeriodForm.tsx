import { useState, type FormEvent } from 'react'
import { parseIsoDate } from '../../../reports/dates'
import FormField from '../../FormField'
import { buttonOutline } from '../../ui'

interface CustomPeriodFormProps {
  from: string
  to: string
  onApply: (from: string, to: string) => void
}

function validate(from: string, to: string): string | null {
  const start = parseIsoDate(from)
  const end = parseIsoDate(to)
  if (!start || !end) return 'Вкажіть обидві дати'
  return start > end ? 'Початок періоду не може бути пізніше за кінець' : null
}

export default function CustomPeriodForm({ from, to, onApply }: CustomPeriodFormProps) {
  const [draft, setDraft] = useState({ from, to })
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    const problem = validate(draft.from, draft.to)
    setError(problem)
    if (!problem) onApply(draft.from, draft.to)
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="flex flex-wrap items-start gap-3">
      <FormField
        label="Від"
        type="date"
        value={draft.from}
        error={error ?? undefined}
        onChange={(event) => setDraft({ ...draft, from: event.target.value })}
      />
      <FormField label="До" type="date" value={draft.to} onChange={(event) => setDraft({ ...draft, to: event.target.value })} />
      <button type="submit" className={`${buttonOutline} mt-6`}>
        Застосувати
      </button>
    </form>
  )
}
