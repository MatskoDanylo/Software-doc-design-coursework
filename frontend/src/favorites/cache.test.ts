import { QueryClient } from '@tanstack/react-query'
import { beforeEach, describe, expect, it } from 'vitest'
import { catalogKeys } from '../api/catalog'
import { favoritesKeys } from '../api/favorites'
import { historyKeys } from '../api/history'
import { recommendationKeys } from '../api/recommendations'
import type { Title, TitleDetail, TitlePage } from '../types/catalog'
import type { HistoryEntry } from '../types/history'
import type { Recommendation, RecommendationFeed } from '../types/recommendation'
import { applyFavorite, restoreSnapshot, snapshotFavorites } from './cache'

function title(id: number, is_favorite = false): Title {
  return {
    id,
    kind: 'movie',
    name: `Title ${id}`,
    description: '',
    year: 2020,
    country: 'Україна',
    rating: 7,
    poster_url: null,
    genres: [],
    is_favorite,
  }
}

const page = (...items: Title[]): TitlePage => ({ items, total: items.length, page: 1, page_size: 20 })
const recommended = (t: Title): Recommendation => ({ ...t, reason: 'Популярне', score: 1 })

let client: QueryClient
const searchKey = catalogKeys.search({ q: 'x' })
const feedKey = recommendationKeys.feed(1, null)
const similarKey = recommendationKeys.similar(9, 1)

beforeEach(() => {
  client = new QueryClient()
  client.setQueryData(searchKey, page(title(1), title(2)))
  client.setQueryData<TitleDetail>(catalogKeys.title(1), { ...title(1), seasons: [] })
  client.setQueryData(favoritesKeys.page(1), page(title(1, true), title(3, true)))
  client.setQueryData<HistoryEntry[]>(historyKeys.all, [
    { title: title(1), episode: null, progress_sec: 10, duration_sec: 100, finished: false, last_watched: '' },
  ])
  client.setQueryData<RecommendationFeed>(feedKey, { strategy: 'hybrid', items: [recommended(title(1))] })
  client.setQueryData<Recommendation[]>(similarKey, [recommended(title(1)), recommended(title(2))])
})

describe('applyFavorite', () => {
  it('marks the title as favorite in every cached view', () => {
    applyFavorite(client, 1, true)

    expect(client.getQueryData<TitlePage>(searchKey)?.items.map((t) => t.is_favorite)).toEqual([true, false])
    expect(client.getQueryData<TitleDetail>(catalogKeys.title(1))?.is_favorite).toBe(true)
    expect(client.getQueryData<HistoryEntry[]>(historyKeys.all)?.[0].title.is_favorite).toBe(true)
    expect(client.getQueryData<RecommendationFeed>(feedKey)?.items[0].is_favorite).toBe(true)
    expect(client.getQueryData<Recommendation[]>(similarKey)?.map((t) => t.is_favorite)).toEqual([true, false])
    expect(client.getQueryData<TitlePage>(favoritesKeys.page(1))?.items).toHaveLength(2)
  })

  it('removes the title from the Favorites page and fixes the total', () => {
    applyFavorite(client, 1, false)

    const favorites = client.getQueryData<TitlePage>(favoritesKeys.page(1))
    expect(favorites?.items.map((t) => t.id)).toEqual([3])
    expect(favorites?.total).toBe(1)
  })

  it('leaves the Favorites total alone when the title was not on the page', () => {
    applyFavorite(client, 42, false)

    expect(client.getQueryData<TitlePage>(favoritesKeys.page(1))?.total).toBe(2)
  })
})

describe('snapshotFavorites / restoreSnapshot', () => {
  it('rolls an optimistic update back', () => {
    const snapshot = snapshotFavorites(client)

    applyFavorite(client, 1, false)
    restoreSnapshot(client, snapshot)

    expect(client.getQueryData<TitlePage>(favoritesKeys.page(1))?.items.map((t) => t.id)).toEqual([1, 3])
    expect(client.getQueryData<TitleDetail>(catalogKeys.title(1))?.is_favorite).toBe(false)
  })
})
