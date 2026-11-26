import { useQueryClient } from '@tanstack/react-query'
import { useCallback } from 'react'
import { playbackKeys } from '../api/playback'
import { useAuth } from '../auth/useAuth'

export function usePlanRefresh() {
  const client = useQueryClient()
  const { refreshUser } = useAuth()

  return useCallback(async () => {
    await refreshUser()
    await client.invalidateQueries({ queryKey: playbackKeys.all })
  }, [client, refreshUser])
}
