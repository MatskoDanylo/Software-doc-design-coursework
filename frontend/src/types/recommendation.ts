import type { Title } from './catalog'

export interface Recommendation extends Title {
  reason: string
  score: number
}

export interface RecommendationFeed {
  strategy: string
  items: Recommendation[]
}
