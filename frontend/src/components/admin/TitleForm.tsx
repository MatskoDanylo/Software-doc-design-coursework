import { useQuery } from '@tanstack/react-query'
import { useId, useState, type FormEvent } from 'react'
import { catalogApi, catalogKeys } from '../../api/catalog'
import { errorMessage } from '../../api/errors'
import { hasErrors } from '../../auth/validation'
import {
  EMPTY_TITLE,
  titleToValues,
  toTitlePayload,
  validateTitle,
  type TitleSubmit,
  type TitleValues,
} from '../../admin/titleForm'
import type { TitleDetail } from '../../types/catalog'
import GenreToggleList from '../catalog/GenreToggleList'
import FormAlert from '../FormAlert'
import FormField from '../FormField'
import SelectField from '../SelectField'
import TextAreaField from '../TextAreaField'
import { buttonPrimary, labelClass } from '../ui'
import { useFormState } from '../useFormState'
import PosterField from './PosterField'

const KIND_OPTIONS = [
  { value: 'movie', label: 'Фільм' },
  { value: 'series', label: 'Серіал' },
]

interface TitleFormProps {
  title?: TitleDetail
  submitLabel: string
  pending: boolean
  onSubmit: (data: TitleSubmit) => Promise<unknown>
}

export default function TitleForm({ title, submitLabel, pending, onSubmit }: TitleFormProps) {
  const countriesId = useId()
  const form = useFormState<TitleValues>(title ? titleToValues(title) : EMPTY_TITLE)
  const [genreIds, setGenreIds] = useState<number[]>(title?.genres.map((genre) => genre.id) ?? [])
  const [poster, setPoster] = useState<File | null>(null)
  const [submitError, setSubmitError] = useState<unknown>(null)
  const genres = useQuery({ queryKey: catalogKeys.genres, queryFn: catalogApi.genres })
  const countries = useQuery({ queryKey: catalogKeys.countries, queryFn: catalogApi.countries })

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const errors = validateTitle(form.values)
    form.setErrors(errors)
    if (hasErrors(errors)) return
    setSubmitError(null)
    onSubmit({ payload: toTitlePayload(form.values, genreIds), poster }).then(
      () => setPoster(null),
      (error: unknown) => {
        setSubmitError(error)
        form.applyServerErrors(error)
      },
    )
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="grid gap-8 lg:grid-cols-[12rem_1fr]">
      <PosterField
        previewId={title?.id ?? 0}
        name={form.values.name}
        currentUrl={title?.poster_url ?? null}
        file={poster}
        onChange={setPoster}
      />
      <div className="space-y-4">
        {submitError !== null && <FormAlert>{errorMessage(submitError)}</FormAlert>}
        <div className="grid gap-4 sm:grid-cols-[1fr_10rem]">
          <FormField label="Назва" maxLength={255} {...form.bind('name')} />
          <SelectField label="Тип" options={KIND_OPTIONS} {...form.bind('kind')} />
        </div>
        <TextAreaField label="Опис" maxLength={5000} {...form.bind('description')} />
        <div className="grid gap-4 sm:grid-cols-3">
          <FormField label="Рік" type="number" inputMode="numeric" min={1880} max={2100} {...form.bind('year')} />
          <FormField label="Країна" list={countriesId} maxLength={100} {...form.bind('country')} />
          <FormField label="Рейтинг" type="number" min={0} max={10} step={0.1} placeholder="0" {...form.bind('rating')} />
        </div>
        <datalist id={countriesId}>
          {countries.data?.map((country) => <option key={country} value={country} />)}
        </datalist>
        <fieldset className="space-y-2">
          <legend className={labelClass}>Жанри</legend>
          {genres.data?.length === 0 && <p className="text-xs text-muted">Жанрів ще немає</p>}
          <GenreToggleList genres={genres.data ?? []} selected={genreIds} onChange={setGenreIds} />
        </fieldset>
        <button type="submit" disabled={pending} className={buttonPrimary}>
          {pending ? 'Збереження…' : submitLabel}
        </button>
      </div>
    </form>
  )
}
