from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from .llm import ask_json

FIELDS = [
    "complaint_source", "customer_name", "product_name", "product_strength",
    "batch_lot_number", "manufacturing_date", "expiry_date", "quantity_affected",
    "complaint_type", "complaint_date", "detailed_complaint_description",
]

class ComplaintState(TypedDict):
    user_text: str
    existing: dict
    complaint: dict
    risk: dict
    assistant_message: str

def extract_or_update(state: ComplaintState):
    system = """You are an AI assistant for a pharmaceutical Customer Complaint module.

Extract complaint information from the user's message and merge it into the existing complaint.

Rules:
1. Never invent a value.
2. If the user corrects a field, replace the old value.
3. Preserve existing values that are not changed.
4. Use YYYY-MM-DD for complete dates when possible.
5. Quantity may include amount and packaging.
6. complaint_type should be a short category such as Product Quality, Packaging,
   Labeling, Delivery, Adverse Event, or Other.
7. Return ONLY valid JSON.

JSON shape:
{
  "complaint": {
    "complaint_source": null,
    "customer_name": null,
    "product_name": null,
    "product_strength": null,
    "batch_lot_number": null,
    "manufacturing_date": null,
    "expiry_date": null,
    "quantity_affected": null,
    "complaint_type": null,
    "complaint_date": null,
    "detailed_complaint_description": null
  },
  "changed_fields": []
}"""

    prompt = f"""Existing complaint:
{state["existing"]}

New user message:
{state["user_text"]}

Extract and merge the new information now."""

    result = ask_json(system, prompt)
    merged = state["existing"].copy()

    for key in FIELDS:
        value = result.get("complaint", {}).get(key)
        if value not in (None, "", "null"):
            merged[key] = value

    changed = result.get("changed_fields", [])
    return {
        "complaint": merged,
        "assistant_message": f"Updated {len(changed)} complaint field(s)."
    }

def assess_risk(state: ComplaintState):
    system = """You are a pharmaceutical complaint triage assistant.
This is a prototype for decision support, not a regulatory or medical decision.

Assess the complaint conservatively from the information available.

Return ONLY JSON:
{
  "severity": "Critical|Major|Minor|Unknown",
  "priority": "High|Medium|Low|Unknown",
  "rationale": "...",
  "recommended_action": "...",
  "investigation_required": true,
  "missing_information": ["..."]
}

Do not claim certainty when important information is missing."""

    result = ask_json(system, f"Complaint:\n{state['complaint']}")
    return {"risk": result}

builder = StateGraph(ComplaintState)
builder.add_node("extract_or_update", extract_or_update)
builder.add_node("assess_risk", assess_risk)
builder.add_edge(START, "extract_or_update")
builder.add_edge("extract_or_update", "assess_risk")
builder.add_edge("assess_risk", END)

complaint_graph = builder.compile()
