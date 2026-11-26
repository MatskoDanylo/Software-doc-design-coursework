import { ApiError } from '../api/client'
import { HYBRID } from '../recommendations/strategies'
import type { AppSettings, AppSettingsPayload } from '../types/settings'

export const WINDOW_MIN = 1
export const WINDOW_MAX = 365
export const WEIGHT_STEP = 0.05

export interface SettingsDraft {
  strategy: string
  weights: Record<string, number>
  windowDays: string
  timezone: string
}

export type SettingsField = keyof SettingsDraft
export type SettingsErrors = Partial<Record<SettingsField, string>>

const SERVER_FIELDS: Record<string, SettingsField> = {
  recommendation_default_strategy: 'strategy',
  hybrid_weights: 'weights',
  popularity_window_days: 'windowDays',
  report_timezone: 'timezone',
}

export function weightCodes(settings: AppSettings): string[] {
  return settings.available_strategies.filter((code) => code !== HYBRID)
}

export function draftFromSettings(settings: AppSettings): SettingsDraft {
  return {
    strategy: settings.recommendation_default_strategy,
    weights: Object.fromEntries(weightCodes(settings).map((code) => [code, settings.hybrid_weights[code] ?? 0])),
    windowDays: String(settings.popularity_window_days),
    timezone: settings.report_timezone,
  }
}

export function validateSettings(draft: SettingsDraft): SettingsErrors {
  const errors: SettingsErrors = {}
  const days = Number(draft.windowDays)
  if (!draft.strategy) errors.strategy = 'Оберіть стратегію'
  if (!Object.values(draft.weights).some((weight) => weight > 0)) errors.weights = 'Хоча б одна вага має бути більшою за 0'
  if (!/^\d+$/.test(draft.windowDays) || days < WINDOW_MIN || days > WINDOW_MAX) {
    errors.windowDays = `Ціле число від ${WINDOW_MIN} до ${WINDOW_MAX}`
  }
  if (!draft.timezone.trim()) errors.timezone = 'Вкажіть часовий пояс'
  return errors
}

export function toPayload(draft: SettingsDraft): AppSettingsPayload {
  return {
    recommendation_default_strategy: draft.strategy,
    hybrid_weights: draft.weights,
    popularity_window_days: Number(draft.windowDays),
    report_timezone: draft.timezone.trim(),
  }
}

export function serverSettingsErrors(error: unknown): SettingsErrors {
  if (!(error instanceof ApiError)) return {}
  if (error.code === 'unknown_timezone') return { timezone: 'Такого часового поясу немає в базі даних' }
  if (error.code !== 'validation_error') return {}
  const errors: SettingsErrors = {}
  for (const detail of error.details) {
    const field = SERVER_FIELDS[String(detail.loc[1])]
    if (field) errors[field] ??= detail.msg
  }
  return errors
}

export function weightShares(weights: Record<string, number>): Record<string, number> {
  const total = Object.values(weights).reduce((sum, weight) => sum + weight, 0)
  return Object.fromEntries(Object.entries(weights).map(([code, weight]) => [code, total ? weight / total : 0]))
}
