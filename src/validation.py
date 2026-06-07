
import re
from typing import Tuple
from src.logger import get_logger

logger = get_logger("validation")



#========================================================================
# דומיינים חד פעמיים — לא שווה לטפל בלידים עם כתובות אלו
#========================================================================
DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "temp-mail.org",
    "throwam.com", "yopmail.com", "fakeinbox.com",
    "trashmail.com", "disposable.com",
}


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
ISRAELI_PHONE_REGEX = re.compile(r"^05\d{8}$")




#========================================================================
# ולידציה על כתובת מייל
#========================================================================
def validate_email(email: str) -> Tuple[bool, str]:
    
    if not email:
        return False, "Email is empty"

    if not EMAIL_REGEX.match(email):
        return False, f"Invalid email format: {email}"

    domain = email.split("@")[1].lower()
    if domain in DISPOSABLE_DOMAINS:
        return False, f"Disposable email domain not allowed: {domain}"

    return True, ""


#========================================================================
# ולידציה על טלפון
#========================================================================
def validate_phone(phone: str) -> Tuple[bool, str]:
   
    if not phone:
        return False, "Phone is empty"

    cleaned = re.sub(r"[\s\-]", "", phone)

    if not ISRAELI_PHONE_REGEX.match(cleaned):
        return False, f"Invalid Israeli phone: {phone} (must be 05X + 7 digits)"

    return True, ""


#========================================================================
# ולידציה על ליד
#========================================================================
def validate_lead(lead: dict) -> Tuple[bool, list[str]]:
    
    errors = []

    
    if not lead.get("FirstName", "").strip():
        errors.append("FirstName is required")

    if not lead.get("LastName", "").strip():
        errors.append("LastName is required")

    branch_id = lead.get("BranchID", "").strip()
    if not branch_id:
        errors.append("BranchID is required")
    elif not branch_id.isdigit():
        errors.append(f"BranchID must be numeric, got: {branch_id!r}")

    
    email = lead.get("Email", "").strip()
    phone = lead.get("Phone", "").strip()

    email_valid, email_error = validate_email(email) if email else (False, "Email is empty")
    phone_valid, phone_error = validate_phone(phone) if phone else (False, "Phone is empty")

    if not email_valid and not phone_valid:
        errors.append(
            f"At least one valid contact method required. "
            f"Email: {email_error}. Phone: {phone_error}."
        )

    return len(errors) == 0, errors