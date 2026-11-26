import { useId } from 'react'

interface QualitySelectProps {
  heights: number[]
  selected: number | null
  active: number | null
  onSelect: (height: number | null) => void
}

const AUTO = 'auto'

export default function QualitySelect({ heights, selected, active, onSelect }: QualitySelectProps) {
  const id = useId()
  const autoLabel = selected === null && active !== null ? `Авто (${active}p)` : 'Авто'

  return (
    <div className="flex items-center gap-2 text-sm">
      <label htmlFor={id} className="text-muted">
        Якість
      </label>
      <select
        id={id}
        value={selected === null ? AUTO : String(selected)}
        onChange={(event) => onSelect(event.target.value === AUTO ? null : Number(event.target.value))}
        className="rounded-lg border border-line bg-screen px-2 py-1 text-zinc-100 focus:border-gold focus:outline-none"
      >
        <option value={AUTO}>{autoLabel}</option>
        {heights.map((height) => (
          <option key={height} value={height}>
            {height}p
          </option>
        ))}
      </select>
    </div>
  )
}
