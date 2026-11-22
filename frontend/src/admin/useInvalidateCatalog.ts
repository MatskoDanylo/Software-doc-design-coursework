import { useQueryClient, type QueryKey } from '@tanstack/react-query'
import { useCallback } from 'react'
import { catalogKeys } from '../api/catalog'

export function useInvalidateCatalog() {
  const queryClient = useQueryClient()

  return useCallback(
    (keys: QueryKey[] = [catalogKeys.titles, catalogKeys.countries]) =>
      Promise.all(keys.map((queryKey) => queryClient.invalidateQueries({ queryKey }))),
    [queryClient],
  )
}
