import type { Recommendation, RecommendationFeed } from '../types/recommendation'
import { apiRequest } from './client'

export const SHELF_LIMIT = 12

function feedQuery(strategy: string | null): string {
  const params = new URLSearchParams({ limit: String(SHELF_LIMIT) })
  if (strategy) params.set('strategy', strategy)
  return params.toString()
}

export const recommendationsApi = {
  feed: (strategy: string | null) => apiRequest<RecommendationFeed>(`/api/recommendations?${feedQuery(strategy)}`),
  similar: (titleId: number) => apiRequest<Recommendation[]>(`/api/titles/${titleId}/similar?limit=${SHELF_LIMIT}`),
}

export const recommendationKeys = {
  all: ['recommendations'] as const,
  feed: (viewerId: number | null, strategy: string | null) => ['recommendations', 'feed', viewerId, strategy] as const,
  similar: (titleId: number, viewerId: number | null) => ['recommendations', 'similar', titleId, viewerId] as const,
}
