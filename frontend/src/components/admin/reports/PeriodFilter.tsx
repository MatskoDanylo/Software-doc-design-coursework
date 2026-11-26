import { useState } from 'react'
import { PERIOD_PRESETS, type Period } from '../../../reports/filters'
import { chipClass } from '../../ui'
import CustomPeriodForm from './CustomPeriodForm'

interface PeriodFilterProps {
  period: Period
  range: { dateFrom: string; dateTo: string }
  onChange: (period: Period) => void
}

export default function PeriodFilter({ period, range, onChange }: PeriodFilterProps) {
  const [customOpen, setCustomOpen] = useState(false)
  const showCustom = customOpen || period.type === 'custom'

  const choosePreset = (days: (typeof PERIOD_PRESETS)[number]) => {
    setCustomOpen(false)
    onChange({ type: 'preset', days })
  }

  return (
    <div className="space-y-3">
      <div role="group" aria-label="Період" className="flex flex-wrap gap-2">
        {PERIOD_PRESETS.map((days) => (
          <button
            key={days}
            type="button"
            aria-pressed={!showCustom && period.type === 'preset' && period.days === days}
            className={chipClass(!showCustom && period.type === 'preset' && period.days === days)}
            onClick={() => choosePreset(days)}
          >
            {days} днів
          </button>
        ))}
        <button type="button" aria-pressed={showCustom} className={chipClass(showCustom)} onClick={() => setCustomOpen(true)}>
          Довільний
        </button>
      </div>
      {showCustom && (
        <CustomPeriodForm
          key={`${range.dateFrom}:${range.dateTo}`}
          from={range.dateFrom}
          to={range.dateTo}
          onApply={(from, to) => onChange({ type: 'custom', from, to })}
        />
      )}
    </div>
  )
}
