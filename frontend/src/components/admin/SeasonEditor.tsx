import { useState } from 'react'
import { adminCatalogApi } from '../../api/adminCatalog'
import { nextNumber, numberError, SEASON_MAX, useTitleMutation } from '../../admin/catalogForms'
import type { EpisodePayload } from '../../types/adminCatalog'
import type { Season } from '../../types/catalog'
import { buttonGhost, buttonSmall } from '../ui'
import ConfirmButton from './ConfirmButton'
import EpisodeForm from './EpisodeForm'
import EpisodeRow from './EpisodeRow'
import InlineTextForm from './InlineTextForm'

interface SeasonEditorProps {
  titleId: number
  season: Season
}

function AddEpisode({ titleId, season }: SeasonEditorProps) {
  const create = useTitleMutation(
    titleId,
    (payload: EpisodePayload) => adminCatalogApi.createEpisode(season.id, payload),
    { successToast: 'Епізод додано' },
  )
  const number = nextNumber(season.episodes)

  return (
    <EpisodeForm
      key={number}
      initial={{ number, name: '' }}
      submitLabel="Додати епізод"
      pending={create.isPending}
      error={create.error}
      onSubmit={(payload) => create.mutate(payload)}
    />
  )
}

function SeasonHeader({ titleId, season }: SeasonEditorProps) {
  const [editing, setEditing] = useState(false)
  const renumber = useTitleMutation(titleId, (number: number) => adminCatalogApi.updateSeason(season.id, { number }), {
    successToast: 'Номер сезону змінено',
  })

  if (editing) {
    return (
      <InlineTextForm
        label="Номер сезону"
        type="number"
        initial={String(season.number)}
        submitLabel="Зберегти"
        pending={renumber.isPending}
        error={renumber.error}
        validate={(value) => numberError(value, SEASON_MAX)}
        onSubmit={(value) => renumber.mutate(Number(value), { onSuccess: () => setEditing(false) })}
        onCancel={() => setEditing(false)}
      />
    )
  }

  return (
    <div className="flex items-center gap-2">
      <h3 className="font-medium">Сезон {season.number}</h3>
      <button type="button" className={`${buttonGhost} ${buttonSmall}`} onClick={() => setEditing(true)}>
        Змінити номер
      </button>
    </div>
  )
}

export default function SeasonEditor({ titleId, season }: SeasonEditorProps) {
  const remove = useTitleMutation(titleId, () => adminCatalogApi.deleteSeason(season.id), {
    successToast: `Сезон ${season.number} видалено`,
    errorToast: true,
  })

  return (
    <section aria-label={`Сезон ${season.number}`} className="rounded-xl border border-line bg-screen">
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
        <SeasonHeader titleId={titleId} season={season} />
        <ConfirmButton
          label="Видалити сезон"
          question={`Видалити сезон ${season.number} разом з епізодами?`}
          pending={remove.isPending}
          onConfirm={() => remove.mutate(undefined)}
        />
      </div>      <ol className="divide-y divide-line border-y border-line">
        {season.episodes.map((episode) => (
          <EpisodeRow key={episode.id} titleId={titleId} episode={episode} />
        ))}
        {season.episodes.length === 0 && <li className="px-4 py-2 text-sm text-muted">Епізодів поки немає</li>}
      </ol>
      <div className="px-4 py-3">
        <AddEpisode titleId={titleId} season={season} />
      </div>
    </section>
  )
}
