import { useMutation, useQueryClient } from '@tanstack/react-query'
import { favoritesApi, favoritesKeys } from '../api/favorites'
import { toast } from '../toast/store'
import { applyFavorite, FAVORITE_AWARE_KEYS, restoreSnapshot, snapshotFavorites } from './cache'

export interface FavoriteChange {
  titleId: number
  favorite: boolean
}

export function useFavoriteToggle() {
  const client = useQueryClient()

  return useMutation({
    mutationFn: ({ titleId, favorite }: FavoriteChange) =>
      favorite ? favoritesApi.add(titleId) : favoritesApi.remove(titleId),
    onMutate: async ({ titleId, favorite }: FavoriteChange) => {
      await Promise.all(FAVORITE_AWARE_KEYS.map((queryKey) => client.cancelQueries({ queryKey })))
      const snapshot = snapshotFavorites(client)
      applyFavorite(client, titleId, favorite)
      return { snapshot }
    },
    onSuccess: (_data, { favorite }) => {
      toast.success(favorite ? 'Додано у Вибране' : 'Прибрано з Вибраного')
    },
    onError: (_error, _change, context) => {
      if (context) restoreSnapshot(client, context.snapshot)
    },
    onSettled: () => client.invalidateQueries({ queryKey: favoritesKeys.all }),
    meta: { errorToast: true },
  })
}
