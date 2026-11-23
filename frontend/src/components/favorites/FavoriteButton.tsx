import { useLocation, useNavigate } from 'react-router-dom'
import { errorMessage } from '../../api/errors'
import { useAuth } from '../../auth/useAuth'
import { useFavoriteToggle } from '../../favorites/useFavoriteToggle'
import type { RedirectState } from '../../routes/redirect'
import type { Title } from '../../types/catalog'
import { buttonOutline } from '../ui'
import HeartIcon from './HeartIcon'

interface FavoriteButtonProps {
  title: Pick<Title, 'id' | 'name' | 'is_favorite'>
  variant?: 'icon' | 'labeled'
  className?: string
}

const iconClass =
  'inline-flex size-9 items-center justify-center rounded-full bg-screen/75 backdrop-blur transition-colors hover:bg-screen focus-visible:outline-2 focus-visible:outline-gold disabled:opacity-50'

export default function FavoriteButton({ title, variant = 'icon', className = '' }: FavoriteButtonProps) {
  const { status } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const toggle = useFavoriteToggle()
  const favorite = title.is_favorite
  const label = favorite ? `Прибрати «${title.name}» з вибраного` : `Додати «${title.name}» у вибране`

  const handleClick = () => {
    if (status !== 'authenticated') {
      const state: RedirectState = { from: `${location.pathname}${location.search}` }
      navigate('/login', { state })
      return
    }
    toggle.mutate({ titleId: title.id, favorite: !favorite })
  }

  const tone = favorite ? 'text-gold' : 'text-zinc-200 hover:text-gold'
  if (variant === 'icon') {
    return (
      <button
        type="button"
        aria-label={label}
        aria-pressed={favorite}
        disabled={status === 'loading'}
        onClick={handleClick}
        className={`${iconClass} ${tone} ${className}`}
      >
        <HeartIcon filled={favorite} />
      </button>
    )
  }

  return (
    <div className={`flex flex-wrap items-center gap-3 ${className}`}>
      <button
        type="button"
        aria-label={label}
        aria-pressed={favorite}
        disabled={status === 'loading'}
        onClick={handleClick}
        className={`${buttonOutline} ${favorite ? 'border-gold/60 text-gold' : ''}`}
      >
        <HeartIcon filled={favorite} className="size-4" />
        {favorite ? 'У вибраному' : 'У вибране'}
      </button>
      {toggle.isError && (
        <span role="alert" className="text-xs text-danger">
          {errorMessage(toggle.error)}
        </span>
      )}
    </div>
  )
}
