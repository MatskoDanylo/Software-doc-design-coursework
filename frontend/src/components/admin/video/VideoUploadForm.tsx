import { useId, useState, type FormEvent } from 'react'
import { VIDEO_EXTENSIONS } from '../../../api/adminVideo'
import { videoFileError } from '../../../admin/videoForm'
import { buttonGhost, buttonPrimary, buttonSmall } from '../../ui'

interface VideoUploadFormProps {
  hasVideo: boolean
  disabled: boolean
  pending: boolean
  onUpload: (file: File) => void
}

export default function VideoUploadForm({ hasVideo, disabled, pending, onUpload }: VideoUploadFormProps) {
  const id = useId()
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string>()

  const choose = (selected: File | undefined) => {
    if (!selected) return
    const message = videoFileError(selected)
    setError(message)
    setFile(message ? null : selected)
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (file) onUpload(file)
    setFile(null)
  }

  return (
    <form onSubmit={submit} className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <label htmlFor={id} className={`${buttonGhost} ${buttonSmall} cursor-pointer border border-line`}>
          {hasVideo ? 'Обрати нове відео' : 'Обрати відео'}
        </label>
        <input
          id={id}
          type="file"
          accept={VIDEO_EXTENSIONS.join(',')}
          aria-label="Файл відео"
          className="sr-only"
          disabled={disabled || pending}
          onChange={(event) => {
            choose(event.target.files?.[0])
            event.target.value = ''
          }}
        />
        <button type="submit" className={`${buttonPrimary} ${buttonSmall}`} disabled={!file || disabled || pending}>
          {pending ? 'Завантаження…' : 'Завантажити'}
        </button>
      </div>
      <p className={`text-xs ${error ? 'text-danger' : 'text-muted'}`}>
        {error ?? (file ? `Обрано: ${file.name}` : 'MP4, MKV або MOV. Після завантаження відео конвертується у 360p/720p/1080p')}
      </p>
    </form>
  )
}
