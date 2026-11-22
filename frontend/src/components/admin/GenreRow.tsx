import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { adminCatalogApi } from '../../api/adminCatalog'
import { errorMessage } from '../../api/errors'
import { GENRE_KEYS, GENRE_NAME_MAX, nameError } from '../../admin/catalogForms'
import { useInvalidateCatalog } from '../../admin/useInvalidateCatalog'
import type { Genre } from '../../types/catalog'
import { buttonGhost, buttonSmall } from '../ui'
import ConfirmButton from './ConfirmButton'
import InlineTextForm from './InlineTextForm'

export default function GenreRow({ genre }: { genre: Genre }) {
  const [editing, setEditing] = useState(false)
  const invalidate = useInvalidateCatalog()
  const rename = useMutation({
    mutationFn: (name: string) => adminCatalogApi.updateGenre(genre.id, { name }),
    onSuccess: () => {
      setEditing(false)
      return invalidate(GENRE_KEYS)
    },
  })
  const remove = useMutation({
    mutationFn: () => adminCatalogApi.deleteGenre(genre.id),
    onSuccess: () => invalidate(GENRE_KEYS),
  })

  return (
    <li className="flex flex-wrap items-center justify-between gap-3 py-3">
      {editing ? (
        <div className="flex-1">
          <InlineTextForm
            label={`Нова назва жанру «${genre.name}»`}
            initial={genre.name}
            maxLength={GENRE_NAME_MAX}
            submitLabel="Зберегти"
            pending={rename.isPending}
            error={rename.error}
            validate={(value) => nameError(value, GENRE_NAME_MAX)}
            onSubmit={(name) => rename.mutate(name)}
            onCancel={() => setEditing(false)}
          />
        </div>
      ) : (
        <>
          <span className="font-medium text-zinc-100">{genre.name}</span>
          <div className="flex flex-wrap items-center gap-2">
            {remove.isError && <span className="text-xs text-danger">{errorMessage(remove.error)}</span>}
            <button type="button" className={`${buttonGhost} ${buttonSmall}`} onClick={() => setEditing(true)}>
              Перейменувати
            </button>
            <ConfirmButton
              label="Видалити"
              question={`Видалити жанр «${genre.name}»?`}
              pending={remove.isPending}
              onConfirm={() => remove.mutate()}
            />
          </div>
        </>
      )}
    </li>
  )
}
