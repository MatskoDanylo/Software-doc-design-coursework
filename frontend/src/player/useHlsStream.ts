import Hls from 'hls.js/light'
import { useCallback, useEffect, useRef, useState } from 'react'
import { apiUrl } from '../api/client'
import { tokens } from '../api/tokens'

const HLS_MIME = 'application/vnd.apple.mpegurl'

export type StreamSupport = 'mse' | 'native' | null
export type StreamError = 'unsupported' | 'playback'

export interface StreamOptions {
  authorize?: boolean
  startPosition?: number
  autoPlay?: boolean
}

export interface HlsStream {
  heights: number[]
  selectedHeight: number | null
  activeHeight: number | null
  selectHeight: (height: number | null) => void
  error: StreamError | null
  retry: () => void
  blocked: boolean
  play: () => void
}

export function streamSupport(): StreamSupport {
  if (Hls.isSupported()) return 'mse'
  return document.createElement('video').canPlayType(HLS_MIME) ? 'native' : null
}

function isApiRequest(url: string): boolean {
  return new URL(url, window.location.href).pathname.startsWith('/api/')
}

function authorizeRequest(xhr: XMLHttpRequest, url: string): void {
  const token = tokens.getAccess()
  if (token && isApiRequest(url)) xhr.setRequestHeader('Authorization', `Bearer ${token}`)
}

function withTokenQuery(url: string): string {
  const token = tokens.getAccess()
  if (!token) return url
  return `${url}${url.includes('?') ? '&' : '?'}access_token=${encodeURIComponent(token)}`
}

function uniqueHeights(levels: { height: number }[]): number[] {
  return [...new Set(levels.map((level) => level.height).filter((height) => height > 0))].sort((a, b) => b - a)
}

export function useHlsStream(
  video: HTMLVideoElement | null,
  url: string,
  { authorize = false, startPosition = 0, autoPlay = true }: StreamOptions = {},
): HlsStream {
  const [support] = useState(streamSupport)
  const [heights, setHeights] = useState<number[]>([])
  const [selectedHeight, setSelectedHeight] = useState<number | null>(null)
  const [activeHeight, setActiveHeight] = useState<number | null>(null)
  const [failed, setFailed] = useState(false)
  const [blocked, setBlocked] = useState(false)
  const [attempt, setAttempt] = useState(0)
  const hlsRef = useRef<Hls | null>(null)
  const startRef = useRef(startPosition)

  useEffect(() => {
    if (!video || !support) return
    const source = apiUrl(url)
    const start = () => {
      if (autoPlay) video.play().catch(() => setBlocked(true))
    }

    if (support === 'native') {
      const resume = () => {
        if (startRef.current > 0) video.currentTime = startRef.current
        start()
      }
      const fail = () => setFailed(true)
      video.addEventListener('loadedmetadata', resume, { once: true })
      video.addEventListener('error', fail)
      video.setAttribute('src', authorize ? withTokenQuery(source) : source)
      return () => {
        video.removeEventListener('loadedmetadata', resume)
        video.removeEventListener('error', fail)
        video.removeAttribute('src')
        video.load()
      }
    }

    let recovered = false
    const hls = new Hls({ startPosition: startRef.current, xhrSetup: authorize ? authorizeRequest : undefined })
    hlsRef.current = hls
    hls.on(Hls.Events.MANIFEST_PARSED, (_, data) => {
      setHeights(uniqueHeights(data.levels))
      start()
    })
    hls.on(Hls.Events.LEVEL_SWITCHED, (_, data) => setActiveHeight(hls.levels[data.level]?.height ?? null))
    hls.on(Hls.Events.ERROR, (_, data) => {
      if (!data.fatal) return
      if (data.type === Hls.ErrorTypes.MEDIA_ERROR && !recovered) {
        recovered = true
        hls.recoverMediaError()
        return
      }
      setFailed(true)
    })
    hls.loadSource(source)
    hls.attachMedia(video)
    return () => {
      hls.destroy()
      hlsRef.current = null
    }
  }, [video, url, authorize, autoPlay, support, attempt])

  const selectHeight = useCallback((height: number | null) => {
    setSelectedHeight(height)
    const hls = hlsRef.current
    if (!hls) return
    hls.currentLevel = height === null ? -1 : hls.levels.findIndex((level) => level.height === height)
  }, [])

  const retry = useCallback(() => {
    if (video) startRef.current = video.currentTime || startRef.current
    setFailed(false)
    setHeights([])
    setSelectedHeight(null)
    setAttempt((value) => value + 1)
  }, [video])

  const play = useCallback(() => {
    setBlocked(false)
    video?.play().catch(() => setBlocked(true))
  }, [video])

  const error: StreamError | null = support === null ? 'unsupported' : failed ? 'playback' : null
  return { heights, selectedHeight, activeHeight, selectHeight, error, retry, blocked, play }
}
