"""
Pipeline Orchestrator.

Coordinates the full lead processing flow as a class:
  1. Validate
  2. Lookup branch info (from Excel)
  3. Lookup car info (from car_models.txt)
  4. Enrich via external API (with retry + fallback)
  5. Calculate score
  6. Route (HOT / WARM / COLD)
  7. Build final enriched lead object
  8. Store in database

Design decision: נבחר OOP כדי לעטוף את ה-state (branches, cars) במחלקה אחת
במקום להעביר אותו כפרמטר לכל פונקציה. מקל על תחזוקה והרחבה עתידית.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Tuple, Optional

from src.models import LeadInput, BranchInfo, CarInfo
from src.validation import validate_lead
from src.file_loader import get_branch_info, get_car_info
from src.enrichment import enrich_lead
from src.scoring import calculate_score
from src.routing import route_lead
from src.database import save_lead
from src.logger import get_logger

logger = get_logger("pipeline")




class LeadPipeline:
    """
    מתאם את כל שלבי עיבוד הליד.
    
    מקבל את נתוני הסניפים והרכבים פעם אחת ב-__init__,
    ומשתמש בהם בכל קריאה ל-run() — בלי לטעון מחדש.
    """

    def __init__(
        self,
        branches: dict[str, BranchInfo],
        cars: dict[str, CarInfo],
    ) -> None:
        self.branches = branches
        self.cars = cars

    async def run(self, lead_input: LeadInput) -> Tuple[bool, dict[str, Any]]:
        """
        מריץ את הפייפליין המלא על ליד אחד.

        Returns:
            (True,  enriched_lead_dict)  — עיבוד הצליח
            (False, {lead_id, errors})   — ולידציה נכשלה
        """
        lead_id = str(uuid.uuid4())
        lead_data = lead_input.model_dump()

        logger.info(
            "Pipeline started",
            lead_id=lead_id,
            stage="start",
            name=f"{lead_data.get('FirstName', '')} {lead_data.get('LastName', '')}",
        )



#========================================================================
# ולידציה על ליד
#========================================================================
        is_valid, errors = validate_lead(lead_data)
        if not is_valid:
            logger.warning(
                "Lead rejected",
                lead_id=lead_id,
                stage="validation",
                status="rejected",
                errors=errors,
            )
            return False, {"lead_id": lead_id, "errors": errors}

        logger.info("Validation passed", lead_id=lead_id, stage="validation", status="valid")

        #========================================================================
        # Branch lookup
        #========================================================================
        branch_info: BranchInfo = get_branch_info(self.branches, lead_data.get("BranchID", ""))
        logger.info(
            "Branch resolved",
            lead_id=lead_id,
            stage="file_enrichment",
            branch_id=branch_info.branch_id,
            branch_name=branch_info.name,
        )

        #========================================================================
        # Car lookup
        #========================================================================
        car_info: Optional[CarInfo] = get_car_info(self.cars, lead_data.get("AskedCar", ""))
        logger.info(
            "Car resolved",
            lead_id=lead_id,
            stage="file_enrichment",
            car_found=car_info is not None,
            model=car_info.model_name if car_info else None,
        )

        #========================================================================
        # External API enrichment
        #========================================================================
        enrichment_data: Optional[dict] = None
        try:
            enrichment_data = await enrich_lead(
                email=lead_data.get("Email", ""),
                phone=lead_data.get("Phone", ""),
                area=lead_data.get("Area", ""),
            )
        except Exception as e:
            logger.error(
                "Unexpected enrichment error",
                lead_id=lead_id,
                stage="api_enrichment",
                error=str(e),
            )

        logger.info(
            "API enrichment complete",
            lead_id=lead_id,
            stage="api_enrichment",
            enrichment_available=enrichment_data is not None,
        )

        #========================================================================
        # Scoring
        #========================================================================
        score = calculate_score(enrichment_data, car_info)
        logger.info("Score calculated", lead_id=lead_id, stage="scoring", score=score)

        #========================================================================
        # Routing
        #========================================================================
        priority, assigned_to = route_lead(
            score=score,
            branch_info=branch_info,
            worker_code=lead_data.get("WorkerCode", ""),
        )
        logger.info(
            "Lead routed",
            lead_id=lead_id,
            stage="routing",
            priority=priority,
            assigned_to=assigned_to,
        )

        #========================================================================
        # Build final enriched object
        #========================================================================
        enriched_lead: dict[str, Any] = {
            "lead_id": lead_id,
            "original_lead": lead_data,
            "branch_info": {
                "branch_id": branch_info.branch_id,
                "name": branch_info.name,
                "manager": branch_info.manager,
                "region": branch_info.region,
            },
            "car_info": {
                "model_id": car_info.model_id,
                "model_name": car_info.model_name,
                "category": car_info.category,
                "price_range": car_info.price_range,
            } if car_info else None,
            "enrichment": enrichment_data,
            "score": score,
            "priority": priority,
            "assigned_to": assigned_to,
            "status": "processed",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        #========================================================================
        # Persist
        #========================================================================
        try:
            await save_lead(enriched_lead)
            logger.info(
                "Lead stored",
                lead_id=lead_id,
                stage="storage",
                score=score,
                priority=priority,
                assigned_to=assigned_to,
                status="processed",
            )
        except Exception as e:
            logger.error(
                "Failed to store lead",
                lead_id=lead_id,
                stage="storage",
                error=str(e),
            )
            enriched_lead["status"] = "storage_failed"

        logger.info(
            "Pipeline complete",
            lead_id=lead_id,
            stage="complete",
            score=score,
            priority=priority,
            assigned_to=assigned_to,
            status=enriched_lead["status"],
        )

        return True, enriched_lead