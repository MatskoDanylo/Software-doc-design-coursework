import { useEffect, useState } from 'react'
import { formatClock, secondsUntilSkip } from '../../player/ads'
import { useHlsStream } from '../../player/useHlsStream'
import { buttonPrimary } from '../ui'

interface PrerollAdProps {
  url: string
  onDone: () => void
}

export default function PrerollAd({ url, onDone }: PrerollAdProps) {
  const [video, setVideo] = useState<HTMLVideoElement | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const [duration, setDuration] = useState<number | null>(null)
  const stream = useHlsStream(video, url)
  const wait = secondsUntilSkip(elapsed)

  useEffect(() => {
    if (stream.error) onDone()
  }, [stream.error, onDone])

  return (
    <section aria-label="Реклама" className="relative aspect-video overflow-hidden rounded-xl bg-black">
      <video
        ref={setVideo}
        playsInline
        className="size-full"
        onTimeUpdate={(event) => setElapsed(event.currentTarget.currentTime)}
        onDurationChange={(event) => setDuration(event.currentTarget.duration)}
        onEnded={onDone}
      />
      <div className="absolute top-3 left-3 flex items-center gap-2 rounded-md bg-black/70 px-2.5 py-1 text-xs font-medium text-zinc-100">
        <span className="rounded bg-gold px-1.5 py-0.5 text-screen">Реклама</span>
        {duration !== null && Number.isFinite(duration) && (
          <span aria-label="До кінця реклами">{formatClock(Math.ceil(duration - elapsed))}</span>
        )}
      </div>
      {stream.blocked && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/60">
          <button type="button" className={buttonPrimary} onClick={stream.play}>
            ▶ Відтворити
          </button>
        </div>
      )}
      <button
        type="button"
        onClick={onDone}
        disabled={wait > 0}
        className="absolute right-3 bottom-14 rounded-lg border border-zinc-500 bg-black/75 px-4 py-2 text-sm text-zinc-100 transition-colors enabled:hover:border-gold enabled:hover:text-gold disabled:cursor-not-allowed disabled:text-zinc-400"
      >
        {wait > 0 ? `Пропустити через ${wait}` : 'Пропустити ›'}
      </button>
    </section>
  )
}
