import { SORT_OPTIONS, sortKey } from '../../catalog/filters'
import type { SortField, SortOrder } from '../../types/catalog'
import SelectField from '../SelectField'

interface SortSelectProps {
  sort: SortField
  order: SortOrder | null
  onChange: (sort: SortField, order: SortOrder) => void
}

const options = SORT_OPTIONS.map((option) => ({ value: sortKey(option.sort, option.order), label: option.label }))

export default function SortSelect({ sort, order, onChange }: SortSelectProps) {
  return (
    <SelectField
      label="Сортування"
      options={options}
      value={sortKey(sort, order)}
      onChange={(event) => {
        const option = SORT_OPTIONS.find((item) => sortKey(item.sort, item.order) === event.target.value)
        if (option) onChange(option.sort, option.order)
      }}
    />
  )
}
