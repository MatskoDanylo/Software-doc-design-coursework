export const POPULARITY = 'popularity'
export const HYBRID = 'hybrid'

const STRATEGY_LABELS: Record<string, string> = {
  hybrid: 'Гібридна',
  genre_affinity: 'За улюбленими жанрами',
  similar: 'Схоже на переглянуте',
  popularity: 'Популярне',
}

export function strategyLabel(code: string): string {
  return STRATEGY_LABELS[code] ?? code
}
