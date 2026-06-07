

from src.scoring import calculate_score
from src.models import CarInfo



#========================================================================
# Enrichment Scoring Tests
#========================================================================
def test_high_priority_score():
    enrichment = {"lead_priority": "High"}
    score = calculate_score(enrichment, None)
    assert score == 40

def test_medium_priority_score():
    enrichment = {"lead_priority": "Medium"}
    score = calculate_score(enrichment, None)
    assert score == 20

def test_low_priority_score():
    enrichment = {"lead_priority": "Low"}
    score = calculate_score(enrichment, None)
    assert score == 0

def test_email_trust_high():
    enrichment = {"email_insights": {"trust_level": "High"}}
    score = calculate_score(enrichment, None)
    assert score == 20

def test_phone_verified():
    enrichment = {"phone_insights": {"verified": True}}
    score = calculate_score(enrichment, None)
    assert score == 20

def test_no_enrichment():
    score = calculate_score(None, None)
    assert score == 0


#========================================================================
# Car Scoring Tests
#========================================================================
def test_luxury_car():
    car = CarInfo(
        model_id="1", model_name="Test",
        category="Luxury", price_range="200,000",
        availability="Pre-order"
    )
    score = calculate_score(None, car)
    assert score == 20

def test_electric_car():
    car = CarInfo(
        model_id="1", model_name="Test",
        category="Electric", price_range="200,000",
        availability="Pre-order"
    )
    score = calculate_score(None, car)
    assert score == 15

def test_car_in_stock():
    car = CarInfo(
        model_id="1", model_name="Test",
        category="SUV", price_range="150,000",
        availability="In Stock"
    )
    score = calculate_score(None, car)
    assert score == 10


#========================================================================
# Combined Scoring Tests
#========================================================================
def test_max_score():
    enrichment = {
        "lead_priority": "High",
        "email_insights": {"trust_level": "High"},
        "phone_insights": {"verified": True},
    }
    car = CarInfo(
        model_id="1", model_name="Test",
        category="Luxury", price_range="200,000",
        availability="In Stock"
    )
    score = calculate_score(enrichment, car)
    assert score == 100

def test_score_capped_at_100():
    """ציון לא יכול לעלות מעל 100"""
    enrichment = {
        "lead_priority": "High",
        "email_insights": {"trust_level": "High"},
        "phone_insights": {"verified": True},
    }
    car = CarInfo(
        model_id="1", model_name="Test",
        category="Luxury", price_range="200,000",
        availability="In Stock"
    )
    score = calculate_score(enrichment, car)
    assert score <= 100