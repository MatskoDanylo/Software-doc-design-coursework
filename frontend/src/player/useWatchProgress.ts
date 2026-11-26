import { useEffect } from 'react'
import { playbackApi } from '../api/playback'

export const REPORT_INTERVAL_MS = 10_000

export interface WatchTarget {
  titleId: number
  episodeId: number | null
}

export function useWatchProgress(video: HTMLVideoElement | null, { titleId, episodeId }: WatchTarget): void {
  useEffect(() => {
    if (!video) return
    let lastSent: number | null = null
    let position = 0

    const report = (finished: boolean) => {
      const progress = Math.floor(position)
      if (!finished && (progress === 0 || progress === lastSent)) return
      lastSent = progress
      playbackApi
        .saveProgress({ title_id: titleId, episode_id: episodeId, progress_sec: progress, finished })
        .catch(() => undefined)
    }
    const onTick = () => {
      if (!video.paused && !video.ended) report(false)
    }
    const onPause = () => {
      if (!video.ended) report(false)
    }
    const onEnded = () => report(true)
    const onTime = () => {
      position = video.currentTime
    }

    const timer = window.setInterval(onTick, REPORT_INTERVAL_MS)
    video.addEventListener('timeupdate', onTime)
    video.addEventListener('pause', onPause)
    video.addEventListener('ended', onEnded)
    return () => {
      window.clearInterval(timer)
      video.removeEventListener('timeupdate', onTime)
      video.removeEventListener('pause', onPause)
      video.removeEventListener('ended', onEnded)
      if (!video.ended) report(false)
    }
  }, [video, titleId, episodeId])
}
