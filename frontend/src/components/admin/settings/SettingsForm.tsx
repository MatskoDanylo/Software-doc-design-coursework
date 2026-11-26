import { useState, type FormEvent } from 'react'
import { useSaveSettings } from '../../../admin/settings'
import {
  draftFromSettings,
  serverSettingsErrors,
  toPayload,
  validateSettings,
  WINDOW_MAX,
  WINDOW_MIN,
  type SettingsDraft,
  type SettingsErrors,
} from '../../../admin/settingsForm'
import { errorMessage } from '../../../api/errors'
import { strategyLabel } from '../../../recommendations/strategies'
import type { AppSettings } from '../../../types/settings'
import FormAlert from '../../FormAlert'
import FormField from '../../FormField'
import SelectField from '../../SelectField'
import { buttonPrimary, card } from '../../ui'
import HybridWeights from './HybridWeights'

function hasErrors(errors: SettingsErrors): boolean {
  return Object.values(errors).some(Boolean)
}

export default function SettingsForm({ settings }: { settings: AppSettings }) {
  const save = useSaveSettings()
  const [draft, setDraft] = useState<SettingsDraft>(() => draftFromSettings(settings))
  const [errors, setErrors] = useState<SettingsErrors>({})
  const strategies = settings.available_strategies.map((code) => ({ value: code, label: strategyLabel(code) }))

  const change = (patch: Partial<SettingsDraft>) => {
    setDraft((current) => ({ ...current, ...patch }))
    setErrors((current) => ({ ...current, ...Object.fromEntries(Object.keys(patch).map((key) => [key, undefined])) }))
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    const problems = validateSettings(draft)
    setErrors(problems)
    if (hasErrors(problems)) return
    save.mutate(toPayload(draft), {
      onSuccess: (next) => setDraft(draftFromSettings(next)),
      onError: (error) => setErrors(serverSettingsErrors(error)),
    })
  }

  const formError = save.isError && !hasErrors(serverSettingsErrors(save.error)) ? errorMessage(save.error) : null

  return (
    <form noValidate onSubmit={handleSubmit} className={`${card} max-w-2xl space-y-8`}>
      <div className="grid gap-6 sm:grid-cols-2">
        <SelectField
          label="Стратегія рекомендацій за замовчуванням"
          options={strategies}
          value={draft.strategy}
          error={errors.strategy}
          onChange={(event) => change({ strategy: event.target.value })}
        />
        <FormField
          label="Вікно популярності, днів"
          type="number"
          inputMode="numeric"
          min={WINDOW_MIN}
          max={WINDOW_MAX}
          value={draft.windowDays}
          error={errors.windowDays}
          hint={`Від ${WINDOW_MIN} до ${WINDOW_MAX}. Скільки останніх днів враховує «Популярне»`}
          onChange={(event) => change({ windowDays: event.target.value })}
        />
      </div>
      <HybridWeights
        weights={draft.weights}
        error={errors.weights}
        onChange={(code, value) => change({ weights: { ...draft.weights, [code]: value } })}
      />
      <FormField
        label="Часовий пояс звітів"
        value={draft.timezone}
        error={errors.timezone}
        hint="IANA-назва, наприклад Europe/Kyiv"
        onChange={(event) => change({ timezone: event.target.value })}
      />
      {formError && <FormAlert>{formError}</FormAlert>}
      <button type="submit" className={buttonPrimary} disabled={save.isPending}>
        {save.isPending ? 'Зберігаємо…' : 'Зберегти'}
      </button>
    </form>
  )
}
