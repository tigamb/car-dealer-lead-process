"""
Lead Scoring Module.

Calculates a score from 0 to 100 based on:

  From API enrichment:
    lead_priority = "High"              → +40
    lead_priority = "Medium"            → +20
    lead_priority = "Low"               →  +0
    email_insights.trust_level = "High" → +20
    phone_insights.verified = true      → +20

  From car catalog (car_models.txt):
    category = "Luxury"                 → +20
    category = "Electric"               → +15
    availability = "In Stock"           → +10

  Max possible score = 100
"""


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