export type VideoStatus = 'pending' | 'processing' | 'ready' | 'failed'

export interface VideoAsset {
  id: number
  title_id: number | null
  episode_id: number | null
  status: VideoStatus
  error_message: string | null
  hls_path: string | null
  duration_sec: number | null
}

export interface VideoOwner {
  kind: 'title' | 'episode'
  id: number
}
