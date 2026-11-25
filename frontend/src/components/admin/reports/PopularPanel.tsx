import { chartPoints, findSection } from '../../../reports/sections'
import type { Report } from '../../../types/report'
import RankedBarChart from '../../charts/RankedBarChart'
import SectionView from './SectionView'

export default function PopularPanel({ report }: { report: Report }) {
  const titles = findSection(report, 'titles')
  const genres = findSection(report, 'genres')

  return (
    <div className="space-y-10">
      {titles && (
        <SectionView section={titles} groupBy={report.group_by} chartTitle="Глядачі за тайтлами">
          <RankedBarChart data={chartPoints(titles.rows, 'name', ['viewers'])} dataKey="viewers" name="Глядачі" />
        </SectionView>
      )}
      {genres && (
        <SectionView section={genres} groupBy={report.group_by} chartTitle="Глядачі за жанрами">
          <RankedBarChart data={chartPoints(genres.rows, 'genre', ['viewers'])} dataKey="viewers" name="Глядачі" />
        </SectionView>
      )}
    </div>
  )
}
