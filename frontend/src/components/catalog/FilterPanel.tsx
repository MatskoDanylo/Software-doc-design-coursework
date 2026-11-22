import { useQuery } from '@tanstack/react-query'
import { catalogApi, catalogKeys } from '../../api/catalog'
import { hasActiveFilters, type CatalogFilters } from '../../catalog/filters'
import SelectField, { type SelectOption } from '../SelectField'
import { buttonOutline, labelClass } from '../ui'
import GenreToggleList from './GenreToggleList'
import KindFilter from './KindFilter'
import SearchInput from './SearchInput'
import YearRangeFilter from './YearRangeFilter'

const REFERENCE_STALE_MS = 5 * 60 * 1000
const RATING_STEPS = [5, 6, 7, 8, 9]

interface FilterPanelProps {
  filters: CatalogFilters
  onChange: (patch: Partial<CatalogFilters>) => void
  onReset: () => void
}

function withCurrent(options: SelectOption[], current: string, label: string): SelectOption[] {
  return !current || options.some((option) => option.value === current) ? options : [...options, { value: current, label }]
}

function ratingOptions(current: number | null): SelectOption[] {
  const steps = RATING_STEPS.map((step) => ({ value: String(step), label: `${step}+` }))
  const value = current === null ? '' : String(current)
  return [{ value: '', label: 'Будь-який' }, ...withCurrent(steps, value, `${value}+`)]
}

export default function FilterPanel({ filters, onChange, onReset }: FilterPanelProps) {
  const genres = useQuery({ queryKey: catalogKeys.genres, queryFn: catalogApi.genres, staleTime: REFERENCE_STALE_MS })
  const countries = useQuery({
    queryKey: catalogKeys.countries,
    queryFn: catalogApi.countries,
    staleTime: REFERENCE_STALE_MS,
  })
  const countryOptions = (countries.data ?? []).map((country) => ({ value: country, label: country }))

  return (
    <aside aria-label="Фільтри" className="space-y-5 rounded-2xl border border-line bg-surface p-5">
      <SearchInput
        label="Пошук"
        placeholder="Назва або опис"
        value={filters.q}
        onCommit={(q) => onChange({ q })}
      />
      <KindFilter value={filters.kind} onChange={(kind) => onChange({ kind })} />
      <fieldset className="space-y-2">
        <legend className={labelClass}>Жанри</legend>
        {genres.isError ? (
          <p className="text-xs text-danger">Не вдалося завантажити жанри</p>
        ) : (
          <GenreToggleList
            genres={genres.data ?? []}
            selected={filters.genres}
            onChange={(selected) => onChange({ genres: selected })}
          />
        )}
      </fieldset>
      <YearRangeFilter
        from={filters.yearFrom}
        to={filters.yearTo}
        onChange={(yearFrom, yearTo) => onChange({ yearFrom, yearTo })}
      />
      <SelectField
        label="Країна"
        value={filters.country}
        options={[{ value: '', label: 'Усі країни' }, ...withCurrent(countryOptions, filters.country, filters.country)]}
        onChange={(event) => onChange({ country: event.target.value })}
      />
      <SelectField
        label="Мінімальний рейтинг"
        value={filters.minRating === null ? '' : String(filters.minRating)}
        options={ratingOptions(filters.minRating)}
        onChange={(event) => onChange({ minRating: event.target.value ? Number(event.target.value) : null })}
      />
      {hasActiveFilters(filters) && (
        <button type="button" className={`${buttonOutline} w-full`} onClick={onReset}>
          Скинути фільтри
        </button>
      )}
    </aside>
  )
}
