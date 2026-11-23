import { formatClock } from '../../../player/time'
import type { VideoAsset, VideoStatus } from '../../../types/adminVideo'

const STATUS: Record<VideoStatus | 'none', { label: string; className: string }> = {
  none: { label: 'Відео не завантажено', className: 'border-line text-muted' },
  pending: { label: 'Очікує обробки', className: 'border-sky-500/40 bg-sky-500/10 text-sky-300' },
  processing: { label: 'Обробляється…', className: 'animate-pulse border-sky-500/40 bg-sky-500/10 text-sky-300' },
  ready: { label: 'Готово', className: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300' },
  failed: { label: 'Помилка обробки', className: 'border-danger/50 bg-danger/10 text-danger' },
}

export default function VideoStatusBadge({ asset }: { asset: VideoAsset | null }) {
  const status = STATUS[asset?.status ?? 'none']
  const duration = asset?.status === 'ready' && asset.duration_sec ? ` · ${formatClock(asset.duration_sec)}` : ''

  return (
    <span role="status" className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium ${status.className}`}>
      {status.label}
      {duration}
    </span>
  )
}
