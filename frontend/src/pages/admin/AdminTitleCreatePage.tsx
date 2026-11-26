import { useMutation } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { adminCatalogApi } from '../../api/adminCatalog'
import { errorMessage } from '../../api/errors'
import type { TitleSubmit } from '../../admin/titleForm'
import { useInvalidateCatalog } from '../../admin/useInvalidateCatalog'
import TitleForm from '../../components/admin/TitleForm'
import { card, textLink } from '../../components/ui'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { toast } from '../../toast/store'

async function createWithPoster({ payload, poster }: TitleSubmit) {
  const title = await adminCatalogApi.createTitle(payload)
  if (!poster) {
    toast.success('Тайтл створено')
    return title
  }
  try {
    await adminCatalogApi.uploadPoster(title.id, poster)
    toast.success('Тайтл створено, постер завантажено')
  } catch (error) {
    toast.error(`Тайтл створено, але постер не завантажено: ${errorMessage(error)}`)
  }
  return title
}

export default function AdminTitleCreatePage() {
  useDocumentTitle('Новий тайтл — Адмінка')
  const navigate = useNavigate()
  const invalidate = useInvalidateCatalog()
  const create = useMutation({
    mutationFn: createWithPoster,
    onSuccess: (title) => {
      void invalidate()
      navigate(`/admin/titles/${title.id}`, { replace: true })
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
