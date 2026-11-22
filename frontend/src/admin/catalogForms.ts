import { useMutation } from '@tanstack/react-query'
import { catalogKeys } from '../api/catalog'
import { useInvalidateCatalog } from './useInvalidateCatalog'

export const SEASON_MAX = 100
export const EPISODE_MAX = 1000
export const GENRE_NAME_MAX = 80
export const GENRE_KEYS = [catalogKeys.genres, catalogKeys.titles]

export function numberError(value: string, max: number): string | undefined {
  const number = Number(value)
  return /^\d+$/.test(value.trim()) && number >= 1 && number <= max ? undefined : `Ціле число від 1 до ${max}`
}

export function nameError(value: string, max = 255): string | undefined {
  const name = value.trim()
  if (!name) return 'Вкажіть назву'
  return name.length > max ? `Максимум ${max} символів` : undefined
}

export function nextNumber(items: { number: number }[]): number {
  return items.reduce((max, item) => Math.max(max, item.number), 0) + 1
}

export function useTitleMutation<V>(titleId: number, mutationFn: (variables: V) => Promise<unknown>) {
  const invalidate = useInvalidateCatalog()
  return useMutation({ mutationFn, onSuccess: () => invalidate([catalogKeys.title(titleId)]) })
}
