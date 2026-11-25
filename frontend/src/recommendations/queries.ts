import { useQuery } from '@tanstack/react-query'
import { recommendationKeys, recommendationsApi } from '../api/recommendations'
import { useAuth } from '../auth/useAuth'

export function useRecommendationFeed(strategy: string | null = null) {
  const { user, status } = useAuth()
  return useQuery({
    queryKey: recommendationKeys.feed(user?.id ?? null, strategy),
    queryFn: () => recommendationsApi.feed(strategy),
    enabled: status !== 'loading',
  })
}

export function useSimilarTitles(titleId: number) {
  const { user, status } = useAuth()
  return useQuery({
    queryKey: recommendationKeys.similar(titleId, user?.id ?? null),
    queryFn: () => recommendationsApi.similar(titleId),
    enabled: status !== 'loading',
  })
}
