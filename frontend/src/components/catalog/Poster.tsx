import { useState } from 'react'
import { apiUrl } from '../../api/client'

const GRADIENTS = [
  'from-amber-500/70 via-rose-700/60 to-zinc-900',
  'from-sky-500/70 via-indigo-700/60 to-zinc-900',
  'from-emerald-500/70 via-teal-700/60 to-zinc-900',
  'from-fuchsia-500/70 via-purple-700/60 to-zinc-900',
  'from-orange-500/70 via-red-800/60 to-zinc-900',
  'from-cyan-500/70 via-blue-800/60 to-zinc-900',
]

interface PosterProps {
  id: number
  name: string
  url: string | null
  className?: string
}

export default function Poster({ id, name, url, className = '' }: PosterProps) {
  const [failedUrl, setFailedUrl] = useState<string | null>(null)
  const frame = `relative aspect-[2/3] overflow-hidden rounded-xl bg-surface-raised ${className}`

  if (url && failedUrl !== url) {
    return (
      <div className={frame}>
        <img
          src={apiUrl(url)}
          alt={`Постер: ${name}`}
          loading="lazy"
          className="size-full object-cover"
          onError={() => setFailedUrl(url)}
        />
      </div>
    )
  }

  return (
    <div className={`${frame} bg-gradient-to-br ${GRADIENTS[id % GRADIENTS.length]}`} role="img" aria-label={`Постер: ${name}`}>
      <span className="absolute inset-x-3 bottom-4 line-clamp-4 font-display text-lg leading-tight font-semibold text-white drop-shadow">
        {name}
      </span>
    </div>
  )
}
