import type { QueryClient, QueryKey } from '@tanstack/react-query'
import { catalogKeys } from '../api/catalog'
import { favoritesKeys } from '../api/favorites'
import { historyKeys } from '../api/history'
import type { Title, TitleDetail, TitlePage } from '../types/catalog'
import type { HistoryEntry } from '../types/history'

export type CacheSnapshot = [QueryKey, unknown][]

export const FAVORITE_AWARE_KEYS: QueryKey[] = [catalogKeys.titles, favoritesKeys.all, historyKeys.all]

export function snapshotFavorites(client: QueryClient): CacheSnapshot {
  return FAVORITE_AWARE_KEYS.flatMap((queryKey) => client.getQueriesData({ queryKey }))
}

export function restoreSnapshot(client: QueryClient, snapshot: CacheSnapshot): void {
  for (const [queryKey, data] of snapshot) client.setQueryData(queryKey, data)
}

export function applyFavorite(client: QueryClient, titleId: number, favorite: boolean): void {
  const mark = <T extends Title>(title: T): T => (title.id === titleId ? { ...title, is_favorite: favorite } : title)

  const markCatalog = (data: TitlePage | TitleDetail | undefined): TitlePage | TitleDetail | undefined => {
    if (!data) return data
    return 'items' in data ? { ...data, items: data.items.map(mark) } : mark<TitleDetail>(data)
  }
  client.setQueriesData<TitlePage | TitleDetail>({ queryKey: catalogKeys.titles }, markCatalog)
  client.setQueriesData<TitlePage>({ queryKey: favoritesKeys.all }, (data) => {
    if (!data || favorite) return data
    const items = data.items.filter((title) => title.id !== titleId)
    return { ...data, items, total: data.total - (data.items.length - items.length) }
  })
  client.setQueriesData<HistoryEntry[]>({ queryKey: historyKeys.all }, (data) =>
    data?.map((entry) => ({ ...entry, title: mark(entry.title) })),
  )
}
