import type { TitleKind } from '../../types/catalog'
import { chipClass, labelClass } from '../ui'

const OPTIONS: { value: TitleKind | null; label: string }[] = [
  { value: null, label: 'Усе' },
  { value: 'movie', label: 'Фільми' },
  { value: 'series', label: 'Серіали' },
]

interface KindFilterProps {
  value: TitleKind | null
  onChange: (value: TitleKind | null) => void
}

export default function KindFilter({ value, onChange }: KindFilterProps) {
  return (
    <fieldset className="space-y-1.5">
      <legend className={labelClass}>Тип</legend>
      <div className="flex gap-2">
        {OPTIONS.map((option) => (
          <button
            key={option.label}
            type="button"
            aria-pressed={value === option.value}
            className={chipClass(value === option.value)}
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
    </fieldset>
  )
}
