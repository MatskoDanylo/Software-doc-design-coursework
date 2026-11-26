import { useMutation, useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { adminCatalogApi } from '../../api/adminCatalog'
import { catalogApi, catalogKeys } from '../../api/catalog'
import { errorMessage } from '../../api/errors'
import type { TitleSubmit } from '../../admin/titleForm'
import { useInvalidateCatalog } from '../../admin/useInvalidateCatalog'
import SeasonsManager from '../../components/admin/SeasonsManager'
import TitleForm from '../../components/admin/TitleForm'
import VideoPanel from '../../components/admin/video/VideoPanel'
import PageLoader from '../../components/PageLoader'
import StateMessage from '../../components/StateMessage'
import { card, textLink } from '../../components/ui'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'

function BackLink() {
  return (
    <Link to="/admin/titles" className={`${textLink} text-sm`}>
      ← До списку
    </Link>
  )
}

export default function AdminTitleEditPage() {
  const id = Number(useParams().id)
  const invalidate = useInvalidateCatalog()
  const query = useQuery({ queryKey: catalogKeys.title(id), queryFn: () => catalogApi.title(id), enabled: id > 0 })
  useDocumentTitle(query.data ? `Редагування «${query.data.name}» — Адмінка` : 'Редагування — Адмінка')
  const save = useMutation({
    mutationFn: async ({ payload, poster }: TitleSubmit) => {
      await adminCatalogApi.updateTitle(id, payload)
      if (poster) await adminCatalogApi.uploadPoster(id, poster)
    },
    meta: { successToast: 'Зміни збережено' },
    onSettled: () => invalidate(),
  })

  if (query.isPending && id > 0) return <PageLoader />
  if (!query.data) {
    return <StateMessage tone="error" title="Не вдалося відкрити тайтл" text={query.error ? errorMessage(query.error) : 'Тайтл не знайдено'} action={<BackLink />} />
  }

  const title = query.data
  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <BackLink />
          <h1 className="mt-2 font-display text-3xl font-semibold">{title.name}</h1>
        </div>
        <Link to={`/titles/${title.id}`} className={`${textLink} text-sm`}>
          Відкрити на сайті →
        </Link>
      </div>
      <div className={card}>
        <TitleForm key={title.id} title={title} submitLabel="Зберегти" pending={save.isPending} onSubmit={save.mutateAsync} />
      </div>
      {title.kind === 'movie' ? (
        <section aria-labelledby="video-heading" className={`${card} space-y-4`}>
          <h2 id="video-heading" className="font-display text-xl font-semibold">
            Відео
          </h2>
          <VideoPanel owner={{ kind: 'title', id: title.id }} />
        </section>
      ) : (
        <SeasonsManager title={title} />
      )}
    </section>
  )
}
