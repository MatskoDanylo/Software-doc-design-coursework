import type { VideoAsset, VideoOwner } from '../types/adminVideo'
import { ApiError, apiRequest } from './client'

export const VIDEO_EXTENSIONS = ['.mp4', '.mkv', '.mov']

function ownerPath({ kind, id }: VideoOwner): string {
  return kind === 'title' ? `/api/admin/titles/${id}/video` : `/api/admin/episodes/${id}/video`
}

function videoForm(file: File): FormData {
  const form = new FormData()
  form.append('file', file)
  return form
}

export const adminVideoApi = {
  current: async (owner: VideoOwner): Promise<VideoAsset | null> => {
    try {
      return await apiRequest<VideoAsset>(ownerPath(owner))
    } catch (error) {
      if (error instanceof ApiError && error.code === 'video_asset_not_found') return null
      throw error
    }
  },
  upload: (owner: VideoOwner, file: File) =>
    apiRequest<VideoAsset>(ownerPath(owner), { method: 'POST', body: videoForm(file) }),
}

export const adminVideoKeys = {
  owner: ({ kind, id }: VideoOwner) => ['admin', 'video', kind, id] as const,
}
