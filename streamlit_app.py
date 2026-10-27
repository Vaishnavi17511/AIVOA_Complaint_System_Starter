
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st


# --------------------------------------------------
# 1. Streamlit page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="AI Pharmaceutical Complaint Management",
    page_icon="💊",
    layout="wide",
)

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


# --------------------------------------------------
# 2. Load Streamlit Cloud secrets BEFORE importing
#    backend configuration or creating the Groq client
# --------------------------------------------------

try:
    for key in ("GROQ_API_KEY", "GROQ_MODEL", "DATABASE_URL"):
        if key in st.secrets:
            os.environ[key] = str(st.secrets[key])
except Exception:
    # On a local machine, environment variables or a .env
    # file may supply the configuration instead.
    pass


# --------------------------------------------------
# 3. Import existing backend components
# --------------------------------------------------

try:
    from app.config import settings
    from app.graph import complaint_graph, FIELDS
    from app.document import extract_text
    from app.db import SessionLocal, ComplaintRecord, init_db

except Exception as exc:
    st.error(
        "The backend could not be initialized. "
        "Check your dependencies and configuration."
    )
    st.exception(exc)
    st.stop()


# --------------------------------------------------
# 4. Application header
# --------------------------------------------------

st.title("💊 AI Pharmaceutical Complaint Management")

st.caption(
    "AI-assisted complaint entry, document extraction, "
    "risk assessment, and complaint tracking."
)

st.info(
    "AI-generated complaint assessments are decision-support suggestions. "
    "A qualified reviewer must verify the extracted information and "
    "risk assessment before taking action."
)


# --------------------------------------------------
# 5. Complaint helpers
# --------------------------------------------------

def initial_complaint():
    """Create an empty complaint using the backend field list."""
    return {field: "" for field in FIELDS}


def run_workflow(user_text, existing):
    """Extract/update complaint fields and assess risk."""
    return complaint_graph.invoke(
        {
            "user_text": user_text,
            "existing": existing,
            "complaint": existing,
            "risk": {},
            "assistant_message": "",
        }
    )


def risk_values(risk):
    """Normalize the risk assessment for display and storage."""
    risk = risk or {}

    missing = risk.get("missing_information", [])

    if isinstance(missing, str):
        missing = [
            item.strip()
            for item in missing.split(",")
            if item.strip()
        ]

    return {
        "severity": risk.get("severity", "Unknown"),
        "priority": risk.get("priority", "Unknown"),
        "rationale": risk.get("rationale", ""),
        "recommended_action": risk.get("recommended_action", ""),
        "investigation_required": bool(
            risk.get("investigation_required", True)
        ),
        "missing_information": missing,
    }


def save_complaint(complaint, risk):
    """Save a reviewed complaint to the configured database."""
    values = {
        field: complaint.get(field) or None
        for field in FIELDS
    }

    values.update(
        {
            "severity": risk["severity"],
            "priority": risk["priority"],
            "rationale": risk["rationale"],
            "recommended_action": risk["recommended_action"],
            "investigation_required": risk["investigation_required"],
            "missing_information": ", ".join(
                risk["missing_information"]
            ),
        }
    )

    db = SessionLocal()

    try:
        row = ComplaintRecord(**values)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row.id

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def load_complaints():
    """Retrieve saved complaints for the history page."""
    db = SessionLocal()

    try:
        rows = (
            db.query(ComplaintRecord)
            .order_by(ComplaintRecord.created_at.desc())
            .all()
        )

        result = []

        for row in rows:
            result.append(
                {
                    "ID": row.id,
                    "Customer": row.customer_name,
                    "Product": row.product_name,
                    "Batch / Lot": row.batch_lot_number,
                    "Complaint type": row.complaint_type,
                    "Severity": row.severity,
                    "Priority": row.priority,
                    "Investigation required": (
                        row.investigation_required
                    ),
                    "Created at": (
                        row.created_at.isoformat()
                        if row.created_at
                        else ""
                    ),
                }
            )

        return result

    finally:
        db.close()


def initialize_database():
    """Initialize the database tables."""
    init_db()


# --------------------------------------------------
# 6. Initialize Streamlit session state
# --------------------------------------------------

if "complaint" not in st.session_state:
    st.session_state.complaint = initial_complaint()

if "risk" not in st.session_state:
    st.session_state.risk = {}

if "review_ready" not in st.session_state:
    st.session_state.review_ready = False


# --------------------------------------------------
# 7. Sidebar navigation
# --------------------------------------------------

page = st.sidebar.radio(
    "Navigate",
    [
        "New Complaint",
        "Upload Document",
        "Complaint History",
    ],
)

st.sidebar.divider()
st.sidebar.caption("AI-assisted complaint management prototype")


# --------------------------------------------------
# 8. Complaint history
# --------------------------------------------------

if page == "Complaint History":
    st.subheader("📋 Saved Complaints")

    if st.button("Refresh history"):
        st.rerun()

    try:
        initialize_database()
        records = load_complaints()

        if records:
            st.dataframe(
                pd.DataFrame(records),
                use_container_width=True,
                hide_index=True,
            )

            st.caption(f"Total saved complaints: {len(records)}")

        else:
            st.info("No complaints have been saved yet.")

    except Exception:
        st.error(
            "Could not load complaint history. "
            "Check your database configuration and connectivity."
        )
        st.exception(Exception(
            "See the application logs for database diagnostics."
        ))


# --------------------------------------------------
# 9. New complaint: natural-language entry
# --------------------------------------------------

elif page == "New Complaint":
    st.subheader("📝 Describe a Complaint")

    st.write(
        "Describe the complaint in everyday language. "
        "The AI workflow will extract available details and assess risk."
    )

    message = st.text_area(
        "Complaint description or correction",
        placeholder=(
            "Example: A customer reported that three bottles of "
            "Product X had damaged seals. Batch ABC123..."
        ),
        height=150,
        key="new_complaint_message",
    )

    if st.button("Analyze complaint", type="primary"):
        if not message.strip():
            st.warning("Enter a complaint description first.")

        else:
            with st.spinner(
                "Extracting complaint details and assessing risk..."
            ):
                try:
                    result = run_workflow(
                        message,
                        st.session_state.complaint,
                    )

                    st.session_state.complaint = result.get(
                        "complaint",
                        st.session_state.complaint,
                    )

                    st.session_state.risk = risk_values(
                        result.get("risk", {})
                    )

                    st.session_state.review_ready = True

                    st.success(
                        "Analysis complete. Review the extracted fields below."
                    )

                except Exception:
                    st.error(
                        "AI analysis failed. Check your Groq API key, "
                        "model configuration, and connection."
                    )
                    st.exception(Exception(
                        "The complaint analysis workflow returned an error. "
                        "Consult the application logs for details."
                    ))

    # Show editable fields after successful analysis.
    if st.session_state.review_ready:
        st.divider()
        st.subheader("Review Complaint Details")

        complaint = st.session_state.complaint

        labels = {
            "complaint_source": "Complaint source",
            "customer_name": "Customer name",
            "product_name": "Product name",
            "product_strength": "Product strength",
            "batch_lot_number": "Batch / lot number",
            "manufacturing_date": "Manufacturing date",
            "expiry_date": "Expiry date",
            "quantity_affected": "Quantity affected",
            "complaint_type": "Complaint type",
            "complaint_date": "Complaint date",
            "detailed_complaint_description": "Detailed description",
        }

        with st.form("review_complaint_form"):
            edited = {}
            columns = st.columns(2)

            for index, field in enumerate(FIELDS):
                container = columns[index % 2]

                with container:
                    edited[field] = st.text_area(
                        labels.get(field, field.replace("_", " ").title()),
                        value=str(complaint.get(field) or ""),
                        height=90 if (
                            field == "detailed_complaint_description"
                        ) else 68,
                        key=f"review_{field}",
                    )

            st.divider()
            st.subheader("AI Risk Assessment")

            risk = st.session_state.risk

            st.write(f"**Severity:** {risk.get('severity', 'Unknown')}")
            st.write(f"**Priority:** {risk.get('priority', 'Unknown')}")
            st.write(f"**Rationale:** {risk.get('rationale', '')}")

            st.write(
                "**Recommended action:** "
                f"{risk.get('recommended_action', '')}"
            )

            st.write(
                "**Investigation required:** "
                f"{risk.get('investigation_required', True)}"
            )

            missing = risk.get("missing_information", [])

            st.write(
                "**Missing information:** "
                + (", ".join(missing) if missing else "None listed")
            )

            st.caption(
                "This is a prototype decision-support assessment, "
                "not a final medical, safety, or regulatory determination."
            )

            submitted = st.form_submit_button(
                "Save reviewed complaint",
                type="primary",
            )

        if submitted:
            try:
                initialize_database()

                complaint_id = save_complaint(
                    edited,
                    st.session_state.risk,
                )

                st.success(
                    f"Complaint saved successfully. Record ID: {complaint_id}"
                )

                st.session_state.complaint = initial_complaint()
                st.session_state.risk = {}
                st.session_state.review_ready = False

            except Exception:
                st.error(
                    "Could not save the complaint. "
                    "Check the database URL, database permissions, "
                    "and connectivity."
                )
                st.exception(Exception(
                    "The complaint could not be saved. "
                    "Consult the application logs for details."
                ))


# --------------------------------------------------
# 10. Document upload and extraction
# --------------------------------------------------

elif page == "Upload Document":
    st.subheader("📄 Extract Complaint from a Document")

    st.write(
        "Upload a complaint document. The application supports "
        "PDF, TXT, and EML files."
    )

    uploaded = st.file_uploader(
        "Choose a complaint document",
        type=["pdf", "txt", "eml"],
    )

    if st.button("Extract and assess document", type="primary"):
        if uploaded is None:
            st.warning("Upload a document first.")

        else:
            with st.spinner(
                "Reading the document and assessing the complaint..."
            ):
                try:
                    extracted_text = extract_text(
                        uploaded.name,
                        uploaded.getvalue(),
                    )

                    if not extracted_text.strip():
                        st.error(
                            "No readable text was found. "
                            "Scanned PDFs may require OCR."
                        )

                    else:
                        result = run_workflow(
                            extracted_text,
                            initial_complaint(),
                        )

                        st.session_state.complaint = result.get(
                            "complaint",
                            initial_complaint(),
                        )

                        st.session_state.risk = risk_values(
                            result.get("risk", {})
                        )

                        st.session_state.review_ready = True

                        st.success(
                            "Document analyzed. Open New Complaint "
                            "to review the extracted fields and save "
                            "the complaint."
                        )

                        with st.expander("Extracted document text"):
                            st.text(extracted_text)

                except Exception:
                    st.error(
                        "Document processing failed. Check the file "
                        "format, Groq configuration, and application logs."
                    )
                    st.exception(Exception(
                        "Document processing or AI assessment failed. "
                        "Consult the application logs for details."
                    ))
