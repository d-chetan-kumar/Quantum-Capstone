from fastapi import APIRouter
from app.api.v1.transactions import router as transactions_router
from app.api.v1.models import router as models_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.simulator import router as simulator_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.accounts import router as accounts_router

router = APIRouter()
router.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
router.include_router(models_router, prefix="/models", tags=["models"])
router.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
router.include_router(simulator_router, prefix="/simulator", tags=["simulator"])
router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
router.include_router(accounts_router, prefix="/accounts", tags=["accounts"])

