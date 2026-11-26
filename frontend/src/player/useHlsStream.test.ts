import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { tokens } from '../api/tokens'
import { testTokens } from '../test/utils'
import { useHlsStream, type StreamOptions } from './useHlsStream'

type Listener = (event: string, data: Record<string, unknown>) => void
type HlsConfig = { startPosition: number; xhrSetup?: (xhr: XMLHttpRequest, url: string) => void }

const { FakeHls } = vi.hoisted(() => {
  class FakeHls {
    static supported = true
    static instances: FakeHls[] = []
    static Events = { MANIFEST_PARSED: 'manifestParsed', LEVEL_SWITCHED: 'levelSwitched', ERROR: 'error' }
    static ErrorTypes = { MEDIA_ERROR: 'mediaError', NETWORK_ERROR: 'networkError' }
    static isSupported = () => FakeHls.supported

    listeners = new Map<string, Listener>()
    levels: { height: number }[] = []
    currentLevel = -1
    source: string | null = null
    media: HTMLVideoElement | null = null
    destroyed = false
    recoverMediaError = vi.fn()

    readonly config: HlsConfig

    constructor(config: HlsConfig) {
      this.config = config
      FakeHls.instances.push(this)
    }

    on(event: string, listener: Listener) {
      this.listeners.set(event, listener)
    }

    emit(event: string, data: Record<string, unknown>) {
      this.listeners.get(event)?.(event, data)
    }

    loadSource(source: string) {
      this.source = source
    }

    attachMedia(media: HTMLVideoElement) {
      this.media = media
    }

    destroy() {
      this.destroyed = true
    }
  }
  return { FakeHls }
})

vi.mock('hls.js/light', () => ({ default: FakeHls }))

const URL_PATH = '/api/titles/1/stream/master.m3u8'

function makeVideo(play: () => Promise<void> = () => Promise.resolve()) {
  const video = document.createElement('video')
  video.play = vi.fn(play)
  video.load = vi.fn()
  return video
}

function renderStream(video: HTMLVideoElement | null, options?: StreamOptions) {
  return renderHook(() => useHlsStream(video, URL_PATH, options))
}

const lastHls = () => FakeHls.instances.at(-1)!

function parseManifest(hls: InstanceType<typeof FakeHls>, heights: number[]) {
  hls.levels = heights.map((height) => ({ height }))
  act(() => hls.emit(FakeHls.Events.MANIFEST_PARSED, { levels: hls.levels }))
}

beforeEach(() => {
  FakeHls.supported = true
  FakeHls.instances = []
})

afterEach(() => vi.restoreAllMocks())

describe('useHlsStream with Media Source Extensions', () => {
  it('lists unique qualities from the manifest and starts playback', async () => {
    const video = makeVideo()
    const { result } = renderStream(video, { startPosition: 42 })

    const hls = lastHls()
    expect(hls.config.startPosition).toBe(42)
    expect(hls.source).toMatch(/\/api\/titles\/1\/stream\/master\.m3u8$/)
    expect(hls.media).toBe(video)

    parseManifest(hls, [360, 1080, 720, 720, 0])

    expect(result.current.heights).toEqual([1080, 720, 360])
    expect(video.play).toHaveBeenCalledOnce()
    expect(result.current.error).toBeNull()
  })

  it('does not autoplay when disabled and reports a blocked autoplay', async () => {
    const quiet = makeVideo()
    renderStream(quiet, { autoPlay: false })
    parseManifest(lastHls(), [720])
    expect(quiet.play).not.toHaveBeenCalled()

    const blockedVideo = makeVideo(() => Promise.reject(new DOMException('blocked', 'NotAllowedError')))
    const { result } = renderStream(blockedVideo)
    parseManifest(lastHls(), [720])
    await act(async () => {})

    expect(result.current.blocked).toBe(true)
    await act(async () => result.current.play())
    expect(blockedVideo.play).toHaveBeenCalledTimes(2)
  })

  it('switches quality by height and back to auto', () => {
    const { result } = renderStream(makeVideo())
    const hls = lastHls()
    parseManifest(hls, [360, 720, 1080])

    act(() => result.current.selectHeight(720))
    expect(result.current.selectedHeight).toBe(720)
    expect(hls.currentLevel).toBe(1)

    act(() => result.current.selectHeight(null))
    expect(result.current.selectedHeight).toBeNull()
    expect(hls.currentLevel).toBe(-1)

    act(() => hls.emit(FakeHls.Events.LEVEL_SWITCHED, { level: 2 }))
    expect(result.current.activeHeight).toBe(1080)
  })

  it('recovers from the first fatal media error and fails on the next one', () => {
    const { result } = renderStream(makeVideo())
    const hls = lastHls()
    const mediaError = { fatal: true, type: FakeHls.ErrorTypes.MEDIA_ERROR }

    act(() => hls.emit(FakeHls.Events.ERROR, { fatal: false, type: FakeHls.ErrorTypes.NETWORK_ERROR }))
    act(() => hls.emit(FakeHls.Events.ERROR, mediaError))
    expect(hls.recoverMediaError).toHaveBeenCalledOnce()
    expect(result.current.error).toBeNull()

    act(() => hls.emit(FakeHls.Events.ERROR, mediaError))
    expect(result.current.error).toBe('playback')
  })

  it('retries from the current position with a fresh player', () => {
    const video = makeVideo()
    const { result } = renderStream(video)
    const first = lastHls()
    parseManifest(first, [720])
    act(() => first.emit(FakeHls.Events.ERROR, { fatal: true, type: FakeHls.ErrorTypes.NETWORK_ERROR }))
    video.currentTime = 95

    act(() => result.current.retry())

    expect(first.destroyed).toBe(true)
    expect(lastHls()).not.toBe(first)
    expect(lastHls().config.startPosition).toBe(95)
    expect(result.current.error).toBeNull()
    expect(result.current.heights).toEqual([])
  })

  it('adds the access token only to API requests when authorized', () => {
    tokens.save(testTokens)
    renderStream(makeVideo(), { authorize: true })
    const xhrSetup = lastHls().config.xhrSetup!
    const api = { setRequestHeader: vi.fn() } as unknown as XMLHttpRequest
    const media = { setRequestHeader: vi.fn() } as unknown as XMLHttpRequest

    xhrSetup(api, '/api/titles/1/stream/720p/index.m3u8')
    xhrSetup(media, '/media/hls/1/720p/seg_000.ts')

    expect(api.setRequestHeader).toHaveBeenCalledWith('Authorization', 'Bearer access-token')
    expect(media.setRequestHeader).not.toHaveBeenCalled()
  })

  it('does not set up authorization for public streams and waits for the video element', () => {
    renderStream(null)
    expect(FakeHls.instances).toHaveLength(0)

    const { unmount } = renderStream(makeVideo())
    expect(lastHls().config.xhrSetup).toBeUndefined()

    unmount()
    expect(lastHls().destroyed).toBe(true)
  })
})

describe('useHlsStream fallbacks', () => {
  it('uses native HLS with the token in the query string', () => {
    FakeHls.supported = false
    vi.spyOn(HTMLMediaElement.prototype, 'canPlayType').mockReturnValue('maybe')
    tokens.save(testTokens)
    const video = makeVideo()

    const { result, unmount } = renderStream(video, { authorize: true, startPosition: 30 })

    expect(FakeHls.instances).toHaveLength(0)
    expect(video.getAttribute('src')).toMatch(/master\.m3u8\?access_token=access-token$/)
    act(() => video.dispatchEvent(new Event('loadedmetadata')))
    expect(video.currentTime).toBe(30)
    expect(video.play).toHaveBeenCalledOnce()

    act(() => video.dispatchEvent(new Event('error')))
    expect(result.current.error).toBe('playback')

    unmount()
    expect(video.hasAttribute('src')).toBe(false)
    expect(video.load).toHaveBeenCalled()
  })

  it('reports browsers without HLS support', () => {
    FakeHls.supported = false
    vi.spyOn(HTMLMediaElement.prototype, 'canPlayType').mockReturnValue('')

    const { result } = renderStream(makeVideo())

    expect(result.current.error).toBe('unsupported')
    expect(FakeHls.instances).toHaveLength(0)
  })
})
