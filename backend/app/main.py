from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import AIRequest, AIResponse, SaveComplaintRequest
from .graph import complaint_graph
from .document import extract_text
from .db import SessionLocal, ComplaintRecord, init_db


app = FastAPI(
    title="Complaint Management API"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


def run_ai(text: str, complaint: dict):
    return complaint_graph.invoke({
        "user_text": text,
        "existing": complaint,
        "complaint": complaint,
        "risk": {},
        "assistant_message": "",
    })


@app.get("/api/health")
def health():
    return {
        "status": "ok"
    }


@app.post(
    "/api/complaints/ai",
    response_model=AIResponse
)
def ai_complaint(request: AIRequest):

    result = run_ai(
        request.text,
        request.complaint.model_dump()
    )

    return {
        "complaint": result["complaint"],
        "risk": result["risk"],
        "assistant_message": result["assistant_message"],
    }


@app.post(
    "/api/complaints/extract",
    response_model=AIResponse
)
async def extract_complaint(
    file: UploadFile = File(...)
):

    data = await file.read()

    try:
        text = extract_text(
            file.filename or "document",
            data
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="No readable text found."
        )

    result = run_ai(
        text,
        {}
    )

    return {
        "complaint": result["complaint"],
        "risk": result["risk"],
        "assistant_message":
            "Complaint extracted from the uploaded document.",
    }


@app.post("/api/complaints/save")
def save_complaint(
    request: SaveComplaintRequest
):

    c = request.complaint
    r = request.risk

    db = SessionLocal()

    try:

        row = ComplaintRecord(

            # --------------------------------
            # COMPLAINT FORM PARAMETERS
            # --------------------------------

            complaint_source=c.complaint_source,

            customer_name=c.customer_name,

            product_name=c.product_name,

            product_strength=c.product_strength,

            batch_lot_number=c.batch_lot_number,

            manufacturing_date=c.manufacturing_date,

            expiry_date=c.expiry_date,

            quantity_affected=c.quantity_affected,

            complaint_type=c.complaint_type,

            complaint_date=c.complaint_date,

            detailed_complaint_description=
                c.detailed_complaint_description,

            # --------------------------------
            # AI RISK ASSESSMENT PARAMETERS
            # --------------------------------

            severity=r.severity,

            priority=r.priority,

            rationale=r.rationale,

            recommended_action=
                r.recommended_action,

            investigation_required=
                r.investigation_required,

            missing_information=
                ", ".join(r.missing_information)
        )

        db.add(row)

        db.commit()

        db.refresh(row)

        return {
            "id": row.id,
            "status": "saved"
        }

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


@app.get("/api/complaints")
def get_complaints():

    db = SessionLocal()

    try:

        complaints = (
            db.query(ComplaintRecord)
            .order_by(
                ComplaintRecord.created_at.desc()
            )
            .all()
        )

        return [
            {
                "id": complaint.id,

                "complaint_source":
                    complaint.complaint_source,

                "customer_name":
                    complaint.customer_name,

                "product_name":
                    complaint.product_name,

                "product_strength":
                    complaint.product_strength,

                "batch_lot_number":
                    complaint.batch_lot_number,

                "manufacturing_date":
                    complaint.manufacturing_date,

                "expiry_date":
                    complaint.expiry_date,

                "quantity_affected":
                    complaint.quantity_affected,

                "complaint_type":
                    complaint.complaint_type,

                "complaint_date":
                    complaint.complaint_date,

                "detailed_complaint_description":
                    complaint.detailed_complaint_description,

                "severity":
                    complaint.severity,

                "priority":
                    complaint.priority,

                "rationale":
                    complaint.rationale,

                "recommended_action":
                    complaint.recommended_action,

                "investigation_required":
                    complaint.investigation_required,

                "missing_information":
                    complaint.missing_information,

                "created_at":
                    complaint.created_at.isoformat()
                    if complaint.created_at
                    else None,
            }

            for complaint in complaints
        ]

    finally:

        db.close()