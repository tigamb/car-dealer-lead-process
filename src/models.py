
from typing import Optional, Any
from pydantic import BaseModel


#========================================================================
# ליד שנכנס
#========================================================================
class LeadInput(BaseModel):
    BranchID: Optional[str] = ""
    WorkerCode: Optional[str] = ""
    AskedCar: Optional[str] = ""
    FirstName: Optional[str] = ""
    LastName: Optional[str] = ""
    Email: Optional[str] = ""
    Phone: Optional[str] = ""
    FromWebSite: Optional[str] = ""
    Area: Optional[str] = ""
    # שדות נוספים שמגיעים מה-sample_leads.json
    ProductType: Optional[str] = ""
    Remarks: Optional[str] = ""
    Banner: Optional[str] = ""
    IsAllowGetMail: Optional[str] = ""
    Url: Optional[str] = ""



#========================================================================
# נתונים עסקיים
#========================================================================
class BranchInfo(BaseModel):
    branch_id: str
    name: str
    manager: str
    region: str


class CarInfo(BaseModel):
    model_id: str
    model_name: str
    category: str
    price_range: str
    availability: str



#========================================================================
# תשובות API
#========================================================================
class LeadResponse(BaseModel):
    # תשובה כשהליד התקבל ועובד בהצלחה — HTTP 202
    lead_id: str
    status: str = "accepted"
    message: str = "Lead accepted and processed successfully"
    score: int
    priority: str
    assigned_to: str


class LeadRejectedResponse(BaseModel):
    # תשובה כשהליד נדחה בולידציה — HTTP 422
    lead_id: str
    status: str = "rejected"
    message: str = "Lead validation failed"
    errors: list[str]


class LeadListResponse(BaseModel):
    # תשובה לבקשת רשימת כל הלידים
    count: int
    leads: list[dict[str, Any]]


class HealthResponse(BaseModel):
    # תשובת health check — האם השרת עובד
    status: str = "healthy"
    branches_loaded: int
    cars_loaded: int