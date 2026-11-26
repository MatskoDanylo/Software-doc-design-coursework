export interface AppSettingsPayload {
  recommendation_default_strategy: string
  hybrid_weights: Record<string, number>
  popularity_window_days: number
  report_timezone: string
}

export interface AppSettings extends AppSettingsPayload {
  available_strategies: string[]
  updated_at: string | null
}
