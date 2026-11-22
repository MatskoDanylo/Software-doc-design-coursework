import type { Genre, TitleDetail, TitlePage, TitleSearchParams } from '../types/catalog'
import { apiRequest } from './client'

export function toQueryString(params: TitleSearchParams): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === '') continue
    for (const item of Array.isArray(value) ? value : [value]) search.append(key, String(item))
  }
  const query = search.toString()
  return query ? `?${query}` : ''
}

export const catalogApi = {
  search: (params: TitleSearchParams) =>
    apiRequest<TitlePage>(`/api/titles${toQueryString(params)}`, { auth: false }),
  title: (id: number) => apiRequest<TitleDetail>(`/api/titles/${id}`, { auth: false }),
  genres: () => apiRequest<Genre[]>('/api/genres', { auth: false }),
  countries: () => apiRequest<string[]>('/api/countries', { auth: false }),
}

export const catalogKeys = {
  titles: ['titles'] as const,
  search: (params: TitleSearchParams) => ['titles', 'search', params] as const,
  title: (id: number) => ['titles', 'detail', id] as const,
  genres: ['genres'] as const,
  countries: ['countries'] as const,
}
