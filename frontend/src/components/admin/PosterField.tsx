import { useId, useState } from 'react'
import { POSTER_TYPES, posterFileError } from '../../admin/titleForm'
import { useFilePreview } from '../../hooks/useFilePreview'
import Poster from '../catalog/Poster'
import { buttonGhost, buttonSmall, labelClass } from '../ui'

interface PosterFieldProps {
  previewId: number
  name: string
  currentUrl: string | null
  file: File | null
  onChange: (file: File | null) => void
}

export default function PosterField({ previewId, name, currentUrl, file, onChange }: PosterFieldProps) {
  const id = useId()
  const [error, setError] = useState<string>()
  const { url: preview, show } = useFilePreview(file)

  const handleFile = (selected: File | undefined) => {
    if (!selected) return
    const message = posterFileError(selected)
    setError(message)
    if (message) return
    show(selected)
    onChange(selected)
  }

  return (
    <div className="space-y-3">
      <span className={labelClass}>Постер</span>
      <div className="w-40">
        {preview ? (
          <img src={preview} alt="Новий постер" className="aspect-[2/3] w-full rounded-xl object-cover" />
        ) : (
          <Poster id={previewId} name={name || 'Без назви'} url={currentUrl} />
        )}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <label htmlFor={id} className={`${buttonGhost} ${buttonSmall} cursor-pointer border border-line`}>
          {currentUrl || file ? 'Замінити файл' : 'Обрати файл'}
        </label>
        <input
          id={id}
          type="file"
          accept={POSTER_TYPES.join(',')}
          aria-label="Файл постера"
          className="sr-only"
          onChange={(event) => {
            handleFile(event.target.files?.[0])
            event.target.value = ''
          }}
        />
        {file && (
          <button type="button" className={`${buttonGhost} ${buttonSmall}`} onClick={() => onChange(null)}>
            Не завантажувати
          </button>
        )}
      </div>
      <p className={`text-xs ${error ? 'text-danger' : 'text-muted'}`}>
        {error ?? (file ? `Буде завантажено: ${file.name}` : 'JPEG, PNG або WebP до 5 МБ')}
      </p>
    </div>
  )
}
