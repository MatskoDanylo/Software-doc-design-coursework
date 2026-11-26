import { weightShares } from '../../../admin/settingsForm'
import { strategyLabel } from '../../../recommendations/strategies'
import WeightSlider from './WeightSlider'

interface HybridWeightsProps {
  weights: Record<string, number>
  error?: string
  onChange: (code: string, value: number) => void
}

export default function HybridWeights({ weights, error, onChange }: HybridWeightsProps) {
  const shares = weightShares(weights)

  return (
    <fieldset className="space-y-4" aria-describedby={error ? 'hybrid-weights-error' : undefined}>
      <legend className="text-sm font-medium text-zinc-200">Ваги гібридної стратегії</legend>
      <p className="text-xs text-muted">Від 0 до 1. Відсоток показує частку компонента в сумі ваг; 0 вимикає компонент.</p>
      {Object.entries(weights).map(([code, value]) => (
        <WeightSlider
          key={code}
          label={strategyLabel(code)}
          value={value}
          share={shares[code] ?? 0}
          onChange={(next) => onChange(code, next)}
        />
      ))}
      {error && (
        <p id="hybrid-weights-error" className="text-xs text-danger">
          {error}
        </p>
      )}
    </fieldset>
  )
}
