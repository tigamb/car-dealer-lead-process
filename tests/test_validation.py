"""
Unit tests for the validation module.
Run with: pytest tests/
"""

from src.validation import validate_email, validate_phone, validate_lead


# ── Email Tests ───────────────────────────────────────────────────────────────

def test_valid_email():
    valid, error = validate_email("danny.cohen@gmail.com")
    assert valid == True
    assert error == ""

def test_invalid_email_format():
    valid, error = validate_email("not-an-email")
    assert valid == False
    assert "Invalid email format" in error

def test_disposable_email():
    valid, error = validate_email("test@mailinator.com")
    assert valid == False
    assert "Disposable" in error

def test_empty_email():
    valid, error = validate_email("")
    assert valid == False


# ── Phone Tests ───────────────────────────────────────────────────────────────

def test_valid_phone():
    valid, error = validate_phone("0542100319")
    assert valid == True

def test_invalid_phone_too_short():
    valid, error = validate_phone("123")
    assert valid == False

def test_invalid_phone_not_israeli():
    valid, error = validate_phone("0742100319")
    assert valid == False

def test_empty_phone():
    valid, error = validate_phone("")
    assert valid == False


# ── Lead Tests ────────────────────────────────────────────────────────────────

def test_valid_lead():
    lead = {
        "BranchID": "400",
        "FirstName": "דני",
        "LastName": "כהן",
        "Email": "danny@gmail.com",
        "Phone": "0542100319",
    }
    valid, errors = validate_lead(lead)
    assert valid == True
    assert errors == []

def test_lead_missing_contact():
    lead = {
        "BranchID": "400",
        "FirstName": "דני",
        "LastName": "כהן",
        "Email": "",
        "Phone": "",
    }
    valid, errors = validate_lead(lead)
    assert valid == False
    assert len(errors) == 1

def test_lead_non_numeric_branch():
    lead = {
        "BranchID": "invalid",
        "FirstName": "דני",
        "LastName": "כהן",
        "Email": "danny@gmail.com",
        "Phone": "0542100319",
    }
    valid, errors = validate_lead(lead)
    assert valid == False
    assert any("numeric" in e for e in errors)

def test_lead_missing_name():
    lead = {
        "BranchID": "400",
        "FirstName": "",
        "LastName": "",
        "Email": "danny@gmail.com",
        "Phone": "0542100319",
    }
    valid, errors = validate_lead(lead)
    assert valid == False
    assert len(errors) == 2  # שני שמות חסרים