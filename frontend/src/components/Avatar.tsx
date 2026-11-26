import { useState } from 'react'

interface AvatarProps {
  name: string
  url: string | null
  size?: 'sm' | 'lg'
}

export default function Avatar({ name, url, size = 'sm' }: AvatarProps) {
  const [failedUrl, setFailedUrl] = useState<string | null>(null)
  const sizeClass = size === 'lg' ? 'size-24 text-3xl' : 'size-8 text-sm'

  if (url && url !== failedUrl) {
    return (
      <img
        src={url}
        alt=""
        onError={() => setFailedUrl(url)}
        className={`${sizeClass} shrink-0 rounded-full object-cover ring-1 ring-line`}
      />
    )
  }

  return (
    <span
      aria-hidden="true"
      className={`${sizeClass} inline-flex shrink-0 items-center justify-center rounded-full bg-surface-raised font-semibold text-gold ring-1 ring-line`}
    >
      {name.charAt(0).toUpperCase()}
    </span>
  )
}
