import { ApiError } from '../api/client'
import { errorMessage } from '../api/errors'
import { VIDEO_EXTENSIONS } from '../api/adminVideo'

const UPLOAD_MESSAGES: Record<string, string> = {
  payload_too_large: 'Файл завеликий: перевищено ліміт MAX_VIDEO_UPLOAD_MB на сервері',
  unsupported_media_type: 'Відео має бути файлом MP4, MKV або MOV',
  video_processing: 'Попереднє відео ще обробляється. Дочекайтесь завершення',
  not_a_movie: 'Для серіалу відео завантажується до кожного епізоду',
}

export function videoFileError(file: File): string | undefined {
  const name = file.name.toLowerCase()
  return VIDEO_EXTENSIONS.some((extension) => name.endsWith(extension))
    ? undefined
    : 'Оберіть файл MP4, MKV або MOV'
}

export function uploadErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.code in UPLOAD_MESSAGES) return UPLOAD_MESSAGES[error.code]
  return errorMessage(error)
}
