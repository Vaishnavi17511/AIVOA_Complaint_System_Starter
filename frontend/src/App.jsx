import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  setComplaint,
  setRisk,
  addMessage,
  reset
} from "./store/store";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const fields = [
  ["complaint_source", "Complaint Source"],
  ["customer_name", "Customer Name"],
  ["product_name", "Product Name"],
  ["product_strength", "Product Strength"],
  ["batch_lot_number", "Batch / Lot Number"],
  ["manufacturing_date", "Manufacturing Date"],
  ["expiry_date", "Expiry Date"],
  ["quantity_affected", "Quantity Affected"],
  ["complaint_type", "Complaint Type"],
  ["complaint_date", "Complaint Date"],
  ["detailed_complaint_description", "Detailed Complaint Description"],
];

export default function App() {
  const dispatch = useDispatch();
  const { data, risk, messages } = useSelector((s) => s.complaint);

  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);

  async function runAI() {
    if (!text.trim()) return;

    setLoading(true);
    dispatch(addMessage({ role: "user", text }));

    try {
      const response = await fetch(`${API}/complaints/ai`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, complaint: data })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "AI request failed");
      }

      dispatch(setComplaint(result.complaint));
      dispatch(setRisk(result.risk));
      dispatch(addMessage({ role: "ai", text: result.assistant_message }));
      setText("");
    } catch (error) {
      dispatch(addMessage({ role: "ai", text: `Error: ${error.message}` }));
    } finally {
      setLoading(false);
    }
  }

  async function uploadDocument() {
    if (!file) return;

    setLoading(true);

    try {
      const form = new FormData();
      form.append("file", file);

      const response = await fetch(`${API}/complaints/extract`, {
        method: "POST",
        body: form
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Extraction failed");
      }

      dispatch(setComplaint(result.complaint));
      dispatch(setRisk(result.risk));
      dispatch(addMessage({ role: "ai", text: result.assistant_message }));
    } catch (error) {
      dispatch(addMessage({ role: "ai", text: `Error: ${error.message}` }));
    } finally {
      setLoading(false);
    }
  }

  async function saveComplaint() {
    const response = await fetch(`${API}/complaints/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ complaint: data, risk })
    });

    const result = await response.json();
    alert(result.status === "saved"
      ? `Complaint saved. ID: ${result.id}`
      : "Save failed");
  }

  return (
    <div className="page">
      <header>
        <div>
          <b>AIVOA</b>
          <span> AI Complaint Management</span>
        </div>
        <button onClick={() => dispatch(reset())}>Reset</button>
      </header>

      <main>
        <section className="formPanel">
          <div className="titleRow">
            <div>
              <h1>Log Customer Complaint</h1>
              <p>API & FDF Quality Assurance Module</p>
            </div>
            <span className="badge">Pending Triage</span>
          </div>

          <h3>1. ORIGIN & CUSTOMER DETAILS</h3>
          <div className="grid">
            {fields.slice(0, 2).map(([key, label]) => (
              <AIField key={key} field={key} label={label} data={data} />
            ))}
          </div>

          <h3>2. PRODUCT & BATCH IDENTIFICATION</h3>
          <div className="grid">
            {fields.slice(2, 8).map(([key, label]) => (
              <AIField key={key} field={key} label={label} data={data} />
            ))}
          </div>

          <h3>3. COMPLAINT DETAILS</h3>
          <div className="grid">
            {fields.slice(8, 11).map(([key, label]) => (
              <AIField
                key={key}
                field={key}
                label={label}
                data={data}
                full={key === "detailed_complaint_description"}
              />
            ))}
          </div>



          <button className="save" onClick={saveComplaint}>
            Save Complaint
          </button>
        </section>

        <aside className="assistant">
          <h2>
            ✦ AIVOA Copilot <small>BETA</small>
          </h2>

          <div className="upload">
            <input
              type="file"
              accept=".pdf,.txt,.eml"
              onChange={(e) => setFile(e.target.files[0])}
            />
            <button
              onClick={uploadDocument}
              disabled={!file || loading}
            >
              Extract Complaint
            </button>
            <p>Supported: PDF, TXT, EML</p>
          </div>

          <div className="risk">
            <h3>AI COPILOT RISK ASSESSMENT</h3>
            <p><b>Severity:</b> {risk.severity}</p>
            <p><b>Priority:</b> {risk.priority}</p>
            <p><b>Rationale:</b> {risk.rationale}</p>
            <p><b>Next action:</b> {risk.recommended_action}</p>
            {risk.missing_information?.length > 0 && (
              <p>
                <b>Missing:</b>{" "}
                {risk.missing_information.join(", ")}
              </p>
            )}
          </div>

          <div className="chat">
            {messages.map((message, index) => (
              <div className={message.role} key={index}>
                <b>{message.role === "user" ? "You" : "AI"}</b>
                <p>{message.text}</p>
              </div>
            ))}
          </div>

          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Example: Apollo Pharmacy reported discolored Amoxicillin capsules 500 mg..."
          />

          <button
            className="send"
            onClick={runAI}
            disabled={loading}
          >
            {loading ? "Analyzing..." : "Send to AI"}
          </button>
        </aside>
      </main>
    </div>
  );
}

function AIField({ field, label, data, full }) {
  return (
    <label className={full ? "full" : ""}>
      {label}
      <input
        value={data[field] || ""}
        readOnly
        placeholder="Awaiting AI extraction..."
      />
    </label>
  );
}
