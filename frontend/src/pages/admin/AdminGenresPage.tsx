import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { adminCatalogApi } from '../../api/adminCatalog'
import { catalogApi, catalogKeys } from '../../api/catalog'
import { errorMessage } from '../../api/errors'
import { GENRE_KEYS, GENRE_NAME_MAX, nameError } from '../../admin/catalogForms'
import { useInvalidateCatalog } from '../../admin/useInvalidateCatalog'
import GenreRow from '../../components/admin/GenreRow'
import InlineTextForm from '../../components/admin/InlineTextForm'
import { ListSkeleton } from '../../components/Skeletons'
import StateMessage from '../../components/StateMessage'
import { card } from '../../components/ui'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'

function AddGenre() {
  const [formKey, setFormKey] = useState(0)
  const invalidate = useInvalidateCatalog()
  const create = useMutation({
    mutationFn: (name: string) => adminCatalogApi.createGenre({ name }),
    onSuccess: () => {
      setFormKey((key) => key + 1)
      return invalidate(GENRE_KEYS)
    },
    meta: { successToast: 'Жанр додано' },
  })

  return (
    <InlineTextForm
      key={formKey}
      label="Назва нового жанру"
      maxLength={GENRE_NAME_MAX}
      submitLabel="Додати жанр"
      pending={create.isPending}
      error={create.error}
      validate={(value) => nameError(value, GENRE_NAME_MAX)}
      onSubmit={(name) => create.mutate(name)}
    />
  )
}

export default function AdminGenresPage() {
  useDocumentTitle('Жанри — Адмінка')
  const genres = useQuery({ queryKey: catalogKeys.genres, queryFn: catalogApi.genres })

  return (
    <section className="space-y-6">
      <h1 className="font-display text-3xl font-semibold">Жанри</h1>
      <div className={`${card} space-y-4`}>
        <AddGenre />
        {genres.isPending && <ListSkeleton />}
        {genres.isError && <StateMessage tone="error" title="Не вдалося завантажити жанри" text={errorMessage(genres.error)} />}
        {genres.data?.length === 0 && <p className="text-sm text-muted">Жанрів ще немає</p>}
        {genres.data && genres.data.length > 0 && (
          <ul className="divide-y divide-line">
            {genres.data.map((genre) => (
              <GenreRow key={genre.id} genre={genre} />
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
