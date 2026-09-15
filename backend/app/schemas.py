from typing import Optional
from pydantic import BaseModel, Field

class Complaint(BaseModel):
    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    product_strength: Optional[str] = None
    batch_lot_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    quantity_affected: Optional[str] = None
    complaint_type: Optional[str] = None
    complaint_date: Optional[str] = None
    detailed_complaint_description: Optional[str] = None
    initial_severity: Optional[str] = None
    priority: Optional[str] = None

class RiskAssessment(BaseModel):
    severity: str = "Unknown"
    priority: str = "Unknown"
    rationale: str = ""
    recommended_action: str = ""
    investigation_required: bool = True
    missing_information: list[str] = Field(default_factory=list)

class AIRequest(BaseModel):
    text: str
    complaint: Complaint = Complaint()

class AIResponse(BaseModel):
    complaint: Complaint
    risk: RiskAssessment
    assistant_message: str

class SaveComplaintRequest(BaseModel):
    complaint: Complaint
    risk: RiskAssessment
