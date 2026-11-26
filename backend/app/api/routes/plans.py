from fastapi import APIRouter

from app.api.deps import BillingServiceDep
from app.schemas.billing import PlanRead

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("")
def list_plans(billing: BillingServiceDep) -> list[PlanRead]:
    return [PlanRead.from_quote(quote) for quote in billing.list_plans()]
