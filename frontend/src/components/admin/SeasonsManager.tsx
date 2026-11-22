import { adminCatalogApi } from '../../api/adminCatalog'
import { nextNumber, numberError, SEASON_MAX, useTitleMutation } from '../../admin/catalogForms'
import type { TitleDetail } from '../../types/catalog'
import { card } from '../ui'
import InlineTextForm from './InlineTextForm'
import SeasonEditor from './SeasonEditor'

export default function SeasonsManager({ title }: { title: TitleDetail }) {
  const create = useTitleMutation(title.id, (number: number) => adminCatalogApi.createSeason(title.id, { number }))
  const number = nextNumber(title.seasons)

  return (
    <section aria-labelledby="seasons-admin-heading" className={`${card} space-y-4`}>
      <h2 id="seasons-admin-heading" className="font-display text-xl font-semibold">
        Сезони та епізоди
      </h2>
      {title.seasons.length === 0 && <p className="text-sm text-muted">Сезонів ще немає</p>}
      {title.seasons.map((season) => (
        <SeasonEditor key={season.id} titleId={title.id} season={season} />
      ))}
      <InlineTextForm
        key={number}
        label="Номер нового сезону"
        type="number"
        initial={String(number)}
        submitLabel="Додати сезон"
        pending={create.isPending}
        error={create.error}
        validate={(value) => numberError(value, SEASON_MAX)}
        onSubmit={(value) => create.mutate(Number(value))}
      />
    </section>
  )
}
