import { Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from 'recharts'
import { formatNumber } from '../../reports/format'
import type { ChartPoint } from '../../reports/sections'
import { axisTick, barCursor, GRID_COLOR, SERIES_COLORS, tooltipStyle, type ValueFormat } from './theme'

const ROW_HEIGHT = 30
const MAX_LABEL = 22

function shortLabel(value: string): string {
  return value.length > MAX_LABEL ? `${value.slice(0, MAX_LABEL - 1)}…` : value
}

interface RankedBarChartProps {
  data: ChartPoint[]
  dataKey: string
  name: string
  format?: ValueFormat
}

export default function RankedBarChart({ data, dataKey, name, format = formatNumber }: RankedBarChartProps) {
  const height = Math.max(120, data.length * ROW_HEIGHT + 32)

  return (
    <BarChart responsive data={data} layout="vertical" style={{ width: '100%', height }} margin={{ right: 16 }}>
      <CartesianGrid horizontal={false} stroke={GRID_COLOR} />
      <XAxis type="number" allowDecimals={false} tick={axisTick} stroke={GRID_COLOR} tickFormatter={format} />
      <YAxis type="category" dataKey="label" width={160} interval={0} tick={axisTick} stroke={GRID_COLOR} tickFormatter={shortLabel} />
      <Tooltip {...tooltipStyle} cursor={barCursor} formatter={(value) => format(Number(value))} />
      <Bar dataKey={dataKey} name={name} fill={SERIES_COLORS[0]} radius={[0, 4, 4, 0]} barSize={14} />
    </BarChart>
  )
}
