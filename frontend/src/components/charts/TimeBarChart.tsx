import { Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from 'recharts'
import { formatNumber } from '../../reports/format'
import type { ChartPoint } from '../../reports/sections'
import { axisTick, barCursor, GRID_COLOR, SERIES_COLORS, tooltipStyle, type ValueFormat } from './theme'

interface TimeBarChartProps {
  data: ChartPoint[]
  dataKey: string
  name: string
  format?: ValueFormat
  height?: number
}

export default function TimeBarChart({ data, dataKey, name, format = formatNumber, height = 280 }: TimeBarChartProps) {
  return (
    <BarChart responsive data={data} style={{ width: '100%', height }} margin={{ right: 8 }}>
      <CartesianGrid vertical={false} stroke={GRID_COLOR} />
      <XAxis dataKey="label" minTickGap={16} tick={axisTick} stroke={GRID_COLOR} />
      <YAxis width={64} tick={axisTick} stroke={GRID_COLOR} tickFormatter={format} />
      <Tooltip {...tooltipStyle} cursor={barCursor} formatter={(value) => format(Number(value))} />
      <Bar dataKey={dataKey} name={name} fill={SERIES_COLORS[0]} radius={[4, 4, 0, 0]} maxBarSize={28} />
    </BarChart>
  )
}
