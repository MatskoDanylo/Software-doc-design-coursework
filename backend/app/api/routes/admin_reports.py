from datetime import date

from fastapi import APIRouter, Depends, Response

from app.api.deps import DashboardServiceDep, ReportServiceDep, require_admin
from app.schemas.report import DashboardRead, ReportFormat, ReportRead
from app.services.report_export import CsvReportExporter
from app.services.reports import GroupBy, ReportParams

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/reports/{kind}", response_model=ReportRead)
def get_report(
    kind: str,
    reports: ReportServiceDep,
    date_from: date | None = None,
    date_to: date | None = None,
    group_by: GroupBy | None = None,
    format: ReportFormat = ReportFormat.JSON,
) -> object:
    report = reports.generate(kind, ReportParams(date_from=date_from, date_to=date_to, group_by=group_by))
    if format is ReportFormat.JSON:
        return ReportRead.model_validate(report)
    exporter = CsvReportExporter()
    return Response(
        content=exporter.export(report),
        media_type=exporter.media_type,
        headers={"Content-Disposition": f'attachment; filename="{exporter.filename(report)}"'},
    )


@router.get("/dashboard")
def get_dashboard(dashboard: DashboardServiceDep) -> DashboardRead:
    return DashboardRead.model_validate(dashboard.kpis())
