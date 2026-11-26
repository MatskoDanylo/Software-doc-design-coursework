import { useCallback, useState } from 'react'
import { prerollUrl } from '../../player/ads'
import type { EpisodeRef } from '../../player/episodes'
import type { WatchTarget } from '../../player/useWatchProgress'
import type { Playback } from '../../types/playback'
import NextEpisodeLink from './NextEpisodeLink'
import PrerollAd from './PrerollAd'
import VideoPlayer from './VideoPlayer'

interface PlaybackStageProps {
  playback: Playback
  target: WatchTarget
  next: EpisodeRef | null
}

export default function PlaybackStage({ playback, target, next }: PlaybackStageProps) {
  const preroll = prerollUrl(playback)
  const [adDone, setAdDone] = useState(preroll === null)
  const [ended, setEnded] = useState(false)
  const finishAd = useCallback(() => setAdDone(true), [])
  const finishVideo = useCallback(() => setEnded(true), [])

  return (
    <div className="space-y-4">
      {!adDone && preroll ? (
        <PrerollAd url={preroll} onDone={finishAd} />
      ) : (
        <VideoPlayer
          manifestUrl={playback.manifest_url}
          startPosition={playback.resume_position_sec}
          target={target}
          onEnded={finishVideo}
        />
      )}
      {next && <NextEpisodeLink titleId={target.titleId} episode={next} highlight={ended} />}
    </div>
  )
}
