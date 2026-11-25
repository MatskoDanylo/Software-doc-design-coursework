import { CartesianGrid, Legend, Line, LineChart, Tooltip, XAxis, YAxis } from 'recharts'
import type { ChartPoint } from '../../reports/sections'
import { AXIS_COLOR, axisTick, GRID_COLOR, lineCursor, SERIES_COLORS, tooltipStyle } from './theme'

export interface LineSeries {
  key: string
  name: string
}

interface TimeLineChartProps {
  data: ChartPoint[]
  series: readonly [LineSeries] | readonly [LineSeries, LineSeries]
  height?: number
}

function legendText(value: string) {
  return <span style={{ color: AXIS_COLOR, fontSize: 12 }}>{value}</span>
}

export default function TimeLineChart({ data, series, height = 280 }: TimeLineChartProps) {
  return (
    <LineChart responsive data={data} style={{ width: '100%', height }} margin={{ right: 8 }}>
      <CartesianGrid vertical={false} stroke={GRID_COLOR} />
      <XAxis dataKey="label" minTickGap={24} tick={axisTick} stroke={GRID_COLOR} />
      <YAxis width={40} allowDecimals={false} tick={axisTick} stroke={GRID_COLOR} />
      <Tooltip {...tooltipStyle} cursor={lineCursor} />
      {series.length > 1 && <Legend formatter={legendText} />}
      {series.map((item, index) => (
        <Line
          key={item.key}
          type="monotone"
          dataKey={item.key}
          name={item.name}
          stroke={SERIES_COLORS[index]}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
        />
      ))}
    </LineChart>
  )
}
