import type { ReactNode } from 'react'
import type { GroupBy, ReportSection } from '../../../types/report'
import ChartCard from '../../charts/ChartCard'
import ReportTable from './ReportTable'

interface SectionViewProps {
  section: ReportSection
  groupBy: GroupBy
  chartTitle: string
  children: ReactNode
}

export default function SectionView({ section, groupBy, chartTitle, children }: SectionViewProps) {
  return (
    <section aria-label={section.title} className="space-y-3">
      <h2 className="font-display text-xl font-semibold">{section.title}</h2>
      {section.rows.length > 0 && <ChartCard title={chartTitle}>{children}</ChartCard>}
      <ReportTable section={section} groupBy={groupBy} />
    </section>
  )
}
