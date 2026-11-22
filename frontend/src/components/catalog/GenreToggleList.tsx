import type { Genre } from '../../types/catalog'
import { chipClass } from '../ui'

interface GenreToggleListProps {
  genres: Genre[]
  selected: number[]
  onChange: (selected: number[]) => void
}

export default function GenreToggleList({ genres, selected, onChange }: GenreToggleListProps) {
  const toggle = (id: number) =>
    onChange(selected.includes(id) ? selected.filter((item) => item !== id) : [...selected, id])

  return (
    <div className="flex flex-wrap gap-2">
      {genres.map((genre) => {
        const active = selected.includes(genre.id)
        return (
          <button
            key={genre.id}
            type="button"
            aria-pressed={active}
            className={chipClass(active)}
            onClick={() => toggle(genre.id)}
          >
            {genre.name}
          </button>
        )
      })}
    </div>
  )
}
