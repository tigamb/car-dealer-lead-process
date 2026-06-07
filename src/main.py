
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from src.models import (
    LeadInput,
    LeadResponse,
    LeadRejectedResponse,
    LeadListResponse,
    HealthResponse,
)
from src.logger import setup_logging, get_logger
from src.file_loader import load_branch_config, parse_car_models
from src.database import init_db, get_lead, get_all_leads
from src.pipeline import LeadPipeline

setup_logging()
logger = get_logger("main")


app_state: dict[str, Any] = {
    "pipeline": None,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
   
    
    #========================================================================
    # Startup
    #========================================================================
    logger.info("Starting up")

    branches = load_branch_config("data/branch_config.xlsx")
    cars = parse_car_models("data/car_models.txt")

    # יוצרים instance אחד של הפייפליין — משותף לכל הבקשות
    app_state["pipeline"] = LeadPipeline(branches=branches, cars=cars)

    logger.info(
        "Pipeline ready",
        branch_count=len(branches),
        car_count=len(cars),
    )

    await init_db()
    logger.info("Startup complete")

    yield

    
    #========================================================================
    # Shutdown
    #========================================================================
    logger.info("Shutting down")


app = FastAPI(
    title="Car Dealer Lead Processing Automation",
    description="Production-grade pipeline: Ingestion → Validation → Enrichment → Scoring → Routing → Storage",
    version="1.0.0",
    lifespan=lifespan,
)



#========================================================================
# Endpoints
#========================================================================
@app.post(
    "/api/leads",
    status_code=202,
    response_model=LeadResponse,
    responses={422: {"model": LeadRejectedResponse}},
    summary="Submit a lead for processing",
)
async def submit_lead(lead: LeadInput):
    
    logger.info(
        "Lead received",
        first_name=lead.FirstName,
        last_name=lead.LastName,
        branch_id=lead.BranchID,
    )

    pipeline: LeadPipeline = app_state["pipeline"]
    success, result = await pipeline.run(lead)

    if not success:
        return JSONResponse(
            status_code=422,
            content=LeadRejectedResponse(
                lead_id=result.get("lead_id", ""),
                errors=result.get("errors", []),
            ).model_dump(),
        )

    return LeadResponse(
        lead_id=result["lead_id"],
        score=result["score"],
        priority=result["priority"],
        assigned_to=result["assigned_to"],
    )


@app.get("/api/leads", response_model=LeadListResponse, summary="List all processed leads")
async def list_leads(limit: int = 100, offset: int = 0):
    """מחזיר את כל הלידים עם pagination."""
    leads = await get_all_leads(limit=limit, offset=offset)
    return LeadListResponse(count=len(leads), leads=leads)


@app.get("/api/leads/{lead_id}", summary="Retrieve a specific lead")
async def retrieve_lead(lead_id: str):
    """מחזיר ליד בודד לפי ID."""
    lead = await get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {lead_id!r} not found")
    return lead


@app.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check():
    """בודק שהשרת עובד והנתונים נטענו."""
    pipeline: LeadPipeline = app_state["pipeline"]
    return HealthResponse(
        branches_loaded=len(pipeline.branches),
        cars_loaded=len(pipeline.cars),
    )