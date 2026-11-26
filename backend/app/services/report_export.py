import csv
import io
from datetime import date

from app.services.reports import GroupBy, Report, ReportValue

GROUP_LABELS = {GroupBy.DAY: "по днях", GroupBy.MONTH: "по місяцях"}


class CsvReportExporter:
    media_type = "text/csv; charset=utf-8"
    delimiter = ";"

    def filename(self, report: Report) -> str:
        return f"{report.kind}_{report.date_from.isoformat()}_{report.date_to.isoformat()}.csv"

    def export(self, report: Report) -> bytes:
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=self.delimiter, lineterminator="\r\n")
        writer.writerow([report.title])
        writer.writerow(["Період", f"{report.date_from.isoformat()} — {report.date_to.isoformat()}"])
        writer.writerow(["Групування", GROUP_LABELS[report.group_by]])
        writer.writerow(["Часовий пояс", report.timezone])
        writer.writerow([])
        writer.writerow(["Підсумок"])
        writer.writerows([item.label, self.format(item.value)] for item in report.summary)
        for section in report.sections:
            writer.writerow([])
            writer.writerow([section.title])
            writer.writerow([column.label for column in section.columns])
            writer.writerows([self.format(row.get(c.key)) for c in section.columns] for row in section.rows)
        return ("﻿" + buffer.getvalue()).encode("utf-8")

    @staticmethod
    def format(value: ReportValue) -> str:
        match value:
            case None:
                return ""
            case float():
                return f"{value:.2f}".rstrip("0").rstrip(".").replace(".", ",")
            case date():
                return value.isoformat()
            case _:
                return str(value)
