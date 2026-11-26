import { errorMessage } from '../../../api/errors'
import { isProcessing, useOwnerVideo, useVideoUpload } from '../../../admin/useOwnerVideo'
import { uploadErrorMessage } from '../../../admin/videoForm'
import type { VideoOwner } from '../../../types/adminVideo'
import VideoStatusBadge from './VideoStatusBadge'
import VideoUploadForm from './VideoUploadForm'

export default function VideoPanel({ owner }: { owner: VideoOwner }) {
  const video = useOwnerVideo(owner)
  const upload = useVideoUpload(owner)

  if (video.isPending) return <p className="text-sm text-muted">Перевіряємо відео…</p>
  if (video.isError) return <p className="text-sm text-danger">{errorMessage(video.error)}</p>

  const asset = video.data
  const processing = isProcessing(asset)
  return (
    <div className="space-y-3">
      <VideoStatusBadge asset={asset} />
      {asset?.status === 'failed' && asset.error_message && (
        <p className="text-xs break-words text-danger">{asset.error_message}</p>
      )}
      {processing && (
        <p className="text-xs text-muted">Конвертація виконується у фоні. Сторінку можна закрити, статус оновиться сам</p>
      )}
      <VideoUploadForm
        hasVideo={asset !== null}
        disabled={processing}
        pending={upload.isPending}
        onUpload={(file) => upload.mutate(file)}
      />
      {upload.isError && (
        <p role="alert" className="text-xs text-danger">
          {uploadErrorMessage(upload.error)}
        </p>
      )}
    </div>
  )
}
