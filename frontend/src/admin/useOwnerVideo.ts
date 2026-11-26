import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { adminVideoApi, adminVideoKeys } from '../api/adminVideo'
import { playbackKeys } from '../api/playback'
import type { VideoAsset, VideoOwner } from '../types/adminVideo'

export const POLL_INTERVAL_MS = 2000

export function isProcessing(asset: VideoAsset | null | undefined): boolean {
  return asset?.status === 'pending' || asset?.status === 'processing'
}

export function useOwnerVideo(owner: VideoOwner) {
  return useQuery({
    queryKey: adminVideoKeys.owner(owner),
    queryFn: () => adminVideoApi.current(owner),
    refetchInterval: (query) => (isProcessing(query.state.data) ? POLL_INTERVAL_MS : false),
  })
}

export function useVideoUpload(owner: VideoOwner) {
  const client = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => adminVideoApi.upload(owner, file),
    onSuccess: (asset) => {
      client.setQueryData(adminVideoKeys.owner(owner), asset)
      void client.invalidateQueries({ queryKey: playbackKeys.all })
    },
    meta: { successToast: 'Відео завантажено. Конвертація триває у фоні' },
  })
}
