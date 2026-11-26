import { useState } from 'react'
import { useHlsStream } from '../../player/useHlsStream'
import { useWatchProgress, type WatchTarget } from '../../player/useWatchProgress'
import { buttonPrimary } from '../ui'
import QualitySelect from './QualitySelect'
import StreamError from './StreamError'

interface VideoPlayerProps {
  manifestUrl: string
  startPosition: number
  target: WatchTarget
  onEnded: () => void
}

export default function VideoPlayer({ manifestUrl, startPosition, target, onEnded }: VideoPlayerProps) {
  const [video, setVideo] = useState<HTMLVideoElement | null>(null)
  useWatchProgress(video, target)
  const stream = useHlsStream(video, manifestUrl, { authorize: true, startPosition })

  return (
    <div className="space-y-3">
      <div className="relative aspect-video overflow-hidden rounded-xl bg-black">
        <video ref={setVideo} controls playsInline onEnded={onEnded} className="size-full" aria-label="Відеоплеєр" />
        {stream.blocked && !stream.error && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/60">
            <button type="button" className={buttonPrimary} onClick={stream.play}>
              ▶ Відтворити
            </button>
          </div>
        )}
        {stream.error && <StreamError kind={stream.error} onRetry={stream.retry} />}
      </div>
      {stream.heights.length > 0 && (
        <QualitySelect
          heights={stream.heights}
          selected={stream.selectedHeight}
          active={stream.activeHeight}
          onSelect={stream.selectHeight}
        />
      )}
    </div>
  )
}
