import { useMutation } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { adminCatalogApi } from '../../api/adminCatalog'
import { errorMessage } from '../../api/errors'
import type { AdminNotice } from '../../admin/notice'
import type { TitleSubmit } from '../../admin/titleForm'
import { useInvalidateCatalog } from '../../admin/useInvalidateCatalog'
import TitleForm from '../../components/admin/TitleForm'
import { card, textLink } from '../../components/ui'

async function createWithPoster({ payload, poster }: TitleSubmit) {
  const title = await adminCatalogApi.createTitle(payload)
  if (!poster) return { title, notice: { tone: 'success', text: 'Тайтл створено' } satisfies AdminNotice }
  try {
    await adminCatalogApi.uploadPoster(title.id, poster)
    return { title, notice: { tone: 'success', text: 'Тайтл створено, постер завантажено' } satisfies AdminNotice }
  } catch (error) {
    const text = `Тайтл створено, але постер не завантажено: ${errorMessage(error)}`
    return { title, notice: { tone: 'error', text } satisfies AdminNotice }
  }
}

export default function AdminTitleCreatePage() {
  const navigate = useNavigate()
  const invalidate = useInvalidateCatalog()
  const create = useMutation({
    mutationFn: createWithPoster,
    onSuccess: ({ title, notice }) => {
      void invalidate()
      navigate(`/admin/titles/${title.id}`, { replace: true, state: { notice } })
    },
  })

  return (
    <section className="space-y-6">
      <div>
        <Link to="/admin/titles" className={`${textLink} text-sm`}>
          ← До списку
        </Link>
        <h1 className="mt-2 font-display text-3xl font-semibold">Новий тайтл</h1>
      </div>
      <div className={card}>
        <TitleForm submitLabel="Створити" pending={create.isPending} onSubmit={create.mutateAsync} />
      </div>
    </section>
  )
}
