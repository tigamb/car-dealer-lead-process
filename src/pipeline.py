
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

    def __init__(
        self,
        branches: dict[str, BranchInfo],
        cars: dict[str, CarInfo],
    ) -> None:
        self.branches = branches
        self.cars = cars

    async def run(self, lead_input: LeadInput) -> Tuple[bool, dict[str, Any]]:
       
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

        branch_info: BranchInfo = get_branch_info(self.branches, lead_data.get("BranchID", ""))
        logger.info(
            "Branch resolved",
            lead_id=lead_id,
            stage="file_enrichment",
            branch_id=branch_info.branch_id,
            branch_name=branch_info.name,
        )

        car_info: Optional[CarInfo] = get_car_info(self.cars, lead_data.get("AskedCar", ""))
        logger.info(
            "Car resolved",
            lead_id=lead_id,
            stage="file_enrichment",
            car_found=car_info is not None,
            model=car_info.model_name if car_info else None,
        )

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

        score = calculate_score(enrichment_data, car_info)
        logger.info("Score calculated", lead_id=lead_id, stage="scoring", score=score)

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