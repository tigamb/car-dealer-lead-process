"""
Mock API for Car Dealer Lead Processing

This provides:
1. Lead enrichment service (geographic data, customer insights)

Candidates can use this for testing their automation pipeline.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import random
import asyncio

app = FastAPI(
    title="Car Dealer Mock API",
    description="Mock enrichment and logging API for car dealer lead processing",
    version="1.0.0"
)


# ============================================================================
# MODELS
# ============================================================================

class LeadEnrichmentRequest(BaseModel):
    """Request to enrich a car dealer lead."""
    email: Optional[str] = None
    phone: Optional[str] = None
    area: Optional[str] = None
    asked_car: Optional[str] = None


class LeadEnrichmentResponse(BaseModel):
    """Enriched lead data response."""
    enriched: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ============================================================================
# MOCK DATA - Geographic & Customer Insights
# ============================================================================

# Israeli area codes to cities
AREA_TO_CITY = {
    "1": {"city": "Tel Aviv", "region": "Center", "population": "Large"},
    "2": {"city": "Haifa", "region": "North", "population": "Large"},
    "3": {"city": "Be'er Sheva", "region": "South", "population": "Large"},
    "4": {"city": "Jerusalem", "region": "Center", "population": "Large"},
    "5": {"city": "Netanya", "region": "Center", "population": "Medium"},
    "6": {"city": "Ashdod", "region": "South", "population": "Medium"},
    "7": {"city": "Rishon LeZion", "region": "Center", "population": "Medium"},
    "8": {"city": "Petah Tikva", "region": "Center", "population": "Medium"},
    "9": {"city": "Holon", "region": "Center", "population": "Medium"},
}

# Email domain insights
EMAIL_DOMAIN_INSIGHTS = {
    "gmail.com": {
        "customer_type": "B2C",
        "trust_level": "High",
        "business_email": False
    },
    "walla.co.il": {
        "customer_type": "B2C",
        "trust_level": "High",
        "business_email": False
    },
    "hotmail.com": {
        "customer_type": "B2C",
        "trust_level": "Medium",
        "business_email": False
    },
    "icloud.com": {
        "customer_type": "B2C",
        "trust_level": "High",
        "business_email": False
    },
    "businessmail.co.il": {
        "customer_type": "B2B",
        "trust_level": "High",
        "business_email": True,
        "company_size": "Medium"
    }
}

# Phone prefix insights (Israeli mobile carriers)
PHONE_PREFIX_INSIGHTS = {
    "050": {"carrier": "Pelephone", "quality": "High"},
    "052": {"carrier": "Cellcom", "quality": "High"},
    "053": {"carrier": "Hot Mobile", "quality": "High"},
    "054": {"carrier": "Orange/Partner", "quality": "High"},
    "055": {"carrier": "Hot Mobile", "quality": "High"},
    "058": {"carrier": "Golan Telecom", "quality": "Medium"},
}


# ============================================================================
# ENRICHMENT LOGIC
# ============================================================================

def get_geographic_data(area: Optional[str]) -> Dict[str, Any]:
    """Get geographic data based on area code."""
    if not area or area not in AREA_TO_CITY:
        return {
            "city": "Unknown",
            "region": "Unknown",
            "population": "Unknown",
            "market_potential": "Medium"
        }

    geo_data = AREA_TO_CITY[area].copy()

    # Add market potential based on population
    if geo_data["population"] == "Large":
        geo_data["market_potential"] = "High"
    else:
        geo_data["market_potential"] = "Medium"

    return geo_data


def get_email_insights(email: Optional[str]) -> Dict[str, Any]:
    """Get customer insights based on email domain."""
    if not email or "@" not in email:
        return {
            "customer_type": "Unknown",
            "trust_level": "Low",
            "business_email": False
        }

    domain = email.split("@")[1].lower()

    # Check if we have specific insights for this domain
    if domain in EMAIL_DOMAIN_INSIGHTS:
        return EMAIL_DOMAIN_INSIGHTS[domain].copy()

    # Default insights for unknown domains
    return {
        "customer_type": "B2C",
        "trust_level": "Medium",
        "business_email": False
    }


def get_phone_insights(phone: Optional[str]) -> Dict[str, Any]:
    """Get insights based on phone number."""
    if not phone or len(phone) < 3:
        return {
            "carrier": "Unknown",
            "quality": "Low",
            "verified": False
        }

    # Extract prefix (first 3 digits)
    prefix = phone[:3]

    if prefix in PHONE_PREFIX_INSIGHTS:
        insights = PHONE_PREFIX_INSIGHTS[prefix].copy()
        insights["verified"] = True
        return insights

    return {
        "carrier": "Unknown",
        "quality": "Medium",
        "verified": False
    }


def calculate_lead_priority(enrichment_data: Dict[str, Any]) -> str:
    """Calculate lead priority based on enrichment data."""
    score = 0

    # Geographic scoring
    if enrichment_data.get("geographic", {}).get("market_potential") == "High":
        score += 30

    # Email scoring
    email_insights = enrichment_data.get("email_insights", {})
    if email_insights.get("trust_level") == "High":
        score += 25
    if email_insights.get("business_email"):
        score += 20

    # Phone scoring
    phone_insights = enrichment_data.get("phone_insights", {})
    if phone_insights.get("verified"):
        score += 25

    # Determine priority
    if score >= 70:
        return "High"
    elif score >= 40:
        return "Medium"
    else:
        return "Low"


def generate_enrichment_data(request: LeadEnrichmentRequest) -> Dict[str, Any]:
    """Generate complete enrichment data for a lead."""

    enrichment = {}

    # Geographic enrichment
    if request.area:
        enrichment["geographic"] = get_geographic_data(request.area)

    # Email enrichment
    if request.email:
        enrichment["email_insights"] = get_email_insights(request.email)

    # Phone enrichment
    if request.phone:
        enrichment["phone_insights"] = get_phone_insights(request.phone)

    # Generate additional insights
    enrichment["customer_profile"] = {
        "likely_first_time_buyer": random.choice([True, False]),
        "interest_level": random.choice(["High", "Medium", "Low"]),
        "recommended_contact_time": random.choice([
            "Morning (9-12)",
            "Afternoon (12-16)",
            "Evening (16-19)"
        ])
    }

    # Calculate lead priority
    enrichment["lead_priority"] = calculate_lead_priority(enrichment)

    # Add timestamp
    enrichment["enriched_at"] = datetime.now(timezone.utc).isoformat()

    return enrichment


# ============================================================================
# ENRICHMENT ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "car-dealer-mock-api",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/api/enrich", response_model=LeadEnrichmentResponse)
async def enrich_lead(request: LeadEnrichmentRequest):
    """
    Enrich a car dealer lead with geographic and customer insights.

    Simulates real-world behavior:
    - Random network latency (100ms - 800ms)
    - ~5% chance of temporary failure (for testing retry logic)
    - ~10% chance of no data found
    """

    # Simulate network latency
    await asyncio.sleep(random.uniform(0.1, 0.8))

    # Simulate occasional failures (~5%)
    if random.random() < 0.05:
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable - please retry"
        )

    # Simulate no data found (~10%)
    if random.random() < 0.10:
        return LeadEnrichmentResponse(
            enriched=False,
            error="Insufficient data for enrichment"
        )

    # Generate enrichment data
    enrichment_data = generate_enrichment_data(request)

    return LeadEnrichmentResponse(
        enriched=True,
        data=enrichment_data
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
