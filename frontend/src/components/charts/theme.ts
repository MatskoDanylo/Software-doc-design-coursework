export const SERIES_COLORS = ['#3987e5', '#d95926'] as const
export const AXIS_COLOR = '#9b9bb0'
export const GRID_COLOR = '#2b2b3a'
const TEXT_COLOR = '#e4e4e7'

export const axisTick = { fill: AXIS_COLOR, fontSize: 12 }

export const tooltipStyle = {
  contentStyle: { background: '#1e1e29', border: `1px solid ${GRID_COLOR}`, borderRadius: 8, fontSize: 12 },
  labelStyle: { color: TEXT_COLOR, marginBottom: 4 },
  itemStyle: { color: TEXT_COLOR, padding: 0 },
}

export const barCursor = { fill: 'rgba(255, 255, 255, 0.04)' }
export const lineCursor = { stroke: AXIS_COLOR, strokeDasharray: '3 3' }

export type ValueFormat = (value: number) => string
