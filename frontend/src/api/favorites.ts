import type { TitlePage } from '../types/catalog'
import { apiRequest } from './client'

export const FAVORITES_PAGE_SIZE = 24

export const favoritesApi = {
  list: (page: number) => apiRequest<TitlePage>(`/api/favorites?page=${page}&page_size=${FAVORITES_PAGE_SIZE}`),
  add: (titleId: number) => apiRequest<null>(`/api/favorites/${titleId}`, { method: 'POST' }),
  remove: (titleId: number) => apiRequest<null>(`/api/favorites/${titleId}`, { method: 'DELETE' }),
}

export const favoritesKeys = {
  all: ['favorites'] as const,
  page: (page: number) => ['favorites', page] as const,
}
