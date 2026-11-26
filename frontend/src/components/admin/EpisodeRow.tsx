import { useState } from 'react'
import { adminCatalogApi } from '../../api/adminCatalog'
import { useTitleMutation } from '../../admin/catalogForms'
import { useOwnerVideo } from '../../admin/useOwnerVideo'
import type { EpisodePayload } from '../../types/adminCatalog'
import type { Episode } from '../../types/catalog'
import { buttonGhost, buttonSmall } from '../ui'
import ConfirmButton from './ConfirmButton'
import EpisodeForm from './EpisodeForm'
import VideoPanel from './video/VideoPanel'
import VideoStatusBadge from './video/VideoStatusBadge'

export default function EpisodeRow({ titleId, episode }: { titleId: number; episode: Episode }) {
  const [editing, setEditing] = useState(false)
  const [showVideo, setShowVideo] = useState(false)
  const video = useOwnerVideo({ kind: 'episode', id: episode.id })
  const update = useTitleMutation(
    titleId,
    (payload: EpisodePayload) => adminCatalogApi.updateEpisode(episode.id, payload),
    { successToast: 'Епізод збережено' },
  )
  const remove = useTitleMutation(titleId, () => adminCatalogApi.deleteEpisode(episode.id), {
    successToast: `Епізод ${episode.number} видалено`,
    errorToast: true,
  })

  if (editing) {
    return (
      <li className="px-4 py-2">
        <EpisodeForm
          initial={{ number: episode.number, name: episode.name }}
          submitLabel="Зберегти"
          pending={update.isPending}
          error={update.error}
          onSubmit={(payload) => update.mutate(payload, { onSuccess: () => setEditing(false) })}
          onCancel={() => setEditing(false)}
        />
      </li>
    )
  }

  return (
    <li className="flex flex-wrap items-center gap-3 px-4 py-2 text-sm">
      <span className="w-8 text-muted">{episode.number}</span>
      <span className="flex-1 text-zinc-200">{episode.name}</span>
      {video.isSuccess && <VideoStatusBadge asset={video.data} />}      <button
        type="button"
        aria-expanded={showVideo}
        className={`${buttonGhost} ${buttonSmall}`}
        onClick={() => setShowVideo((value) => !value)}
      >
        Відео
      </button>
      <button type="button" className={`${buttonGhost} ${buttonSmall}`} onClick={() => setEditing(true)}>
        Змінити
      </button>
      <ConfirmButton
        label="Видалити"
        question={`Видалити епізод ${episode.number}?`}
        pending={remove.isPending}
        onConfirm={() => remove.mutate(undefined)}
      />
      {showVideo && (
        <div className="w-full rounded-lg border border-line bg-surface p-4">
          <VideoPanel owner={{ kind: 'episode', id: episode.id }} />
        </div>
      )}
    </li>
  )
}
