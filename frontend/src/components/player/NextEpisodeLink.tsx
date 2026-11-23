import { Link } from 'react-router-dom'
import { episodeLabel, watchPath, type EpisodeRef } from '../../player/episodes'
import { buttonOutline, buttonPrimary } from '../ui'

interface NextEpisodeLinkProps {
  titleId: number
  episode: EpisodeRef
  highlight: boolean
}

export default function NextEpisodeLink({ titleId, episode, highlight }: NextEpisodeLinkProps) {
  return (
    <Link to={watchPath(titleId, episode.id)} className={highlight ? buttonPrimary : buttonOutline}>
      Наступний епізод: {episodeLabel(episode)} →
    </Link>
  )
}
