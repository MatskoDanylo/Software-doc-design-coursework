import { useMutation } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { adminCatalogApi } from '../../api/adminCatalog'
import { errorMessage } from '../../api/errors'
import { useInvalidateCatalog } from '../../admin/useInvalidateCatalog'
import type { Title } from '../../types/catalog'
import Poster from '../catalog/Poster'
import { buttonOutline, buttonSmall } from '../ui'
import ConfirmButton from './ConfirmButton'

const KIND_LABEL = { movie: 'Фільм', series: 'Серіал' } as const

export default function AdminTitleRow({ title }: { title: Title }) {
  const invalidate = useInvalidateCatalog()
  const remove = useMutation({ mutationFn: () => adminCatalogApi.deleteTitle(title.id), onSuccess: () => invalidate() })

  return (
    <tr className="align-middle">
      <td className="py-2 pr-3">
        <Poster id={title.id} name={title.name} url={title.poster_url} className="w-10 rounded-md [&_span]:hidden" />
      </td>
      <td className="py-2 pr-3">
        <Link to={`/admin/titles/${title.id}`} className="font-medium text-zinc-100 hover:text-gold">
          {title.name}
        </Link>
        {remove.isError && <p className="text-xs text-danger">{errorMessage(remove.error)}</p>}
      </td>
      <td className="py-2 pr-3 text-muted">{KIND_LABEL[title.kind]}</td>
      <td className="py-2 pr-3 text-muted">{title.year}</td>
      <td className="py-2 pr-3 text-muted">{title.country}</td>
      <td className="py-2 pr-3 text-gold">{title.rating.toFixed(1)}</td>
      <td className="py-2">
        <div className="flex flex-wrap justify-end gap-2">
          <Link to={`/admin/titles/${title.id}`} className={`${buttonOutline} ${buttonSmall}`}>
            Редагувати
          </Link>
          <ConfirmButton
            label="Видалити"
            question={`Видалити «${title.name}»?`}
            pending={remove.isPending}
            onConfirm={() => remove.mutate()}
          />
        </div>
      </td>
    </tr>
  )
}
