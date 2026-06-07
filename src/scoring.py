
from typing import Optional
from src.models import CarInfo


#========================================================================
# מתודה לחישוב ניקוד
#========================================================================
def calculate_score(enrichment: Optional[dict], car: Optional[CarInfo]) -> int:
    
    score = 0
    #========================================================================
    # ניקוד מה-API
    #========================================================================
    if enrichment:
        lead_priority = enrichment.get("lead_priority", "")
        if lead_priority == "High":
            score += 40
        elif lead_priority == "Medium":
            score += 20

        email_insights = enrichment.get("email_insights", {}) or {}
        if email_insights.get("trust_level") == "High":
            score += 20

        phone_insights = enrichment.get("phone_insights", {}) or {}
        if phone_insights.get("verified") is True:
            score += 20

    
    #========================================================================
    # ניקוד מקובץ הרכבים לפי קטגוריה
    #========================================================================
    if car:
        if car.category == "Luxury":
            score += 20
        elif car.category == "Electric":
            score += 15

        if car.availability == "In Stock":
            score += 10

    return min(score, 100)