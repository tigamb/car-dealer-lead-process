
from typing import Optional
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging
from src.logger import get_logger

logger = get_logger("enrichment")

ENRICH_URL = "http://mock-api:8001/api/enrich"
TIMEOUT_SECONDS = 5.0
MAX_RETRIES = 3



@retry(
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    before_sleep=before_sleep_log(logging.getLogger("enrichment"), logging.WARNING),
    reraise=False,
)
async def _call_enrich_api(email: str, phone: str, area: str) -> Optional[dict]:
    """
    פונקציה פנימית — הקריאה עצמה ל-API עם retry.
    מתחילה ב-_ כי לא אמורים לקרוא לה ישירות מבחוץ.
    """
    payload = {
        "email": email.lower() if email else "",
        "phone": phone.lower() if phone else "",
        "area": area.lower() if area else "",
    }

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        response = await client.post(ENRICH_URL, json=payload)
        response.raise_for_status()  # זורק שגיאה אם status >= 400

        body = response.json()

        
        if not body.get("enriched"):
            logger.info("Enrichment API returned no data", reason=body.get("error"))
            return None

        return body.get("data")


async def enrich_lead(email: str, phone: str, area: str) -> Optional[dict]:
    """
    פונקציה ציבורית — זו שהפייפליין קורא לה.
    עוטפת את _call_enrich_api ומבטיחה שלעולם לא תזרוק exception.
    """
    try:
        data = await _call_enrich_api(email, phone, area)
        if data:
            logger.info("Enrichment succeeded", lead_priority=data.get("lead_priority"))
        return data

    except Exception as e:
        logger.error(
            "Enrichment API failed after all retries, continuing without enrichment",
            error=str(e),
        )
        return None