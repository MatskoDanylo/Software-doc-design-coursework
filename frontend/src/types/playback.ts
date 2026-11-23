export type PlanCode = 'free' | 'premium'

export interface AdBreak {
  enabled: boolean
  preroll_url: string | null
}

export interface Playback {
  plan: PlanCode | null
  manifest_url: string
  ads: AdBreak
  allowed_heights: number[]
  resume_position_sec: number
}

export interface ProgressUpdate {
  title_id: number
  episode_id: number | null
  progress_sec: number
  finished: boolean
}
