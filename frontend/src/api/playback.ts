import type { Playback, ProgressUpdate } from '../types/playback'
import { apiRequest } from './client'

export const playbackApi = {
  get: (titleId: number, episodeId: number | null) =>
    apiRequest<Playback>(`/api/titles/${titleId}/playback${episodeId === null ? '' : `?episode_id=${episodeId}`}`),
  saveProgress: (data: ProgressUpdate) => apiRequest<unknown>('/api/history/progress', { method: 'PUT', body: data }),
}

export const playbackKeys = {
  all: ['playback'] as const,
  detail: (titleId: number, episodeId: number | null) => ['playback', titleId, episodeId] as const,
}
