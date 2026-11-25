import type { Title } from '../types/catalog'
import type { Recommendation, RecommendationFeed } from '../types/recommendation'

export const baseTitle: Title = {
  id: 1,
  kind: 'movie',
  name: 'Тайтл',
  description: '',
  year: 2020,
  country: 'Україна',
  rating: 7.5,
  poster_url: null,
  is_favorite: false,
  genres: [{ id: 1, name: 'Драма' }],
}

export function recommendation(id: number, name: string, reason: string): Recommendation {
  return { ...baseTitle, id, name, reason, score: 1 / id }
}

export const hybridFeed: RecommendationFeed = {
  strategy: 'hybrid',
  items: [
    recommendation(11, 'Дюна', 'Бо ви дивились жанр «Фантастика»'),
    recommendation(12, 'Інтерстеллар', 'Схоже на «Матриця»'),
  ],
}

export const popularFeed: RecommendationFeed = {
  strategy: 'popularity',
  items: [recommendation(21, 'Тіні забутих предків', 'Популярне цього тижня')],
}

export function feedByStrategy(url: URL): Response {
  return Response.json(url.searchParams.get('strategy') === 'popularity' ? popularFeed : hybridFeed)
}
