import type { Plan } from '../types/billing'

export function planFeatures(plan: Plan): string[] {
  return [
    `Якість до ${plan.max_height}p`,
    plan.ads_enabled ? 'Реклама перед відео' : 'Без реклами',
    plan.duration_days === null ? 'Без обмеження в часі' : `Доступ на ${plan.duration_days} днів`,
  ]
}
