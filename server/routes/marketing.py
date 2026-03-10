from fastapi import APIRouter
from services.marketing_hub.agent import load_marketing_plan

router = APIRouter(prefix="/marketing", tags=["Marketing"])

@router.get("/plan")
def get_marketing():
    return {"plan": load_marketing_plan() or []}