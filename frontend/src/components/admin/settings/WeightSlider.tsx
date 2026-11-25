import { useId } from 'react'
import { WEIGHT_STEP } from '../../../admin/settingsForm'
import { formatNumber } from '../../../reports/format'

interface WeightSliderProps {
  label: string
  value: number
  share: number
  onChange: (value: number) => void
}

export default function WeightSlider({ label, value, share, onChange }: WeightSliderProps) {
  const id = useId()

  return (
    <div className="grid grid-cols-[1fr_auto] items-center gap-x-4 gap-y-1">
      <label htmlFor={id} className="text-sm text-zinc-300">
        {label}
      </label>
      <output htmlFor={id} className="text-right text-sm text-zinc-100 tabular-nums">
        {value.toFixed(2)} <span className="text-muted">· {formatNumber(Math.round(share * 100))}%</span>
      </output>
      <input
        id={id}
        type="range"
        min={0}
        max={1}
        step={WEIGHT_STEP}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="col-span-2 w-full accent-gold"
      />
    </div>
  )
}
