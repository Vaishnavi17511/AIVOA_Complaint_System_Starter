import { configureStore, createSlice } from "@reduxjs/toolkit";

const initialComplaint = {
  complaint_source: "",
  customer_name: "",
  product_name: "",
  product_strength: "",
  batch_lot_number: "",
  manufacturing_date: "",
  expiry_date: "",
  quantity_affected: "",
  complaint_type: "",
  complaint_date: "",
  detailed_complaint_description: "",
  initial_severity: "",
  priority: ""
};

const complaintSlice = createSlice({
  name: "complaint",
  initialState: {
    data: initialComplaint,
    risk: {
      severity: "Unknown",
      priority: "Unknown",
      rationale: "",
      recommended_action: "",
      investigation_required: true,
      missing_information: []
    },
    messages: []
  },
  reducers: {
    setComplaint: (state, action) => {
      state.data = { ...state.data, ...action.payload };
    },
    setRisk: (state, action) => {
      state.risk = action.payload;
    },
    addMessage: (state, action) => {
      state.messages.push(action.payload);
    },
    reset: (state) => {
      state.data = initialComplaint;
      state.risk = {
        severity: "Unknown",
        priority: "Unknown",
        rationale: "",
        recommended_action: "",
        investigation_required: true,
        missing_information: []
      };
      state.messages = [];
    }
  }
});

export const { setComplaint, setRisk, addMessage, reset } =
  complaintSlice.actions;

export const store = configureStore({
  reducer: {
    complaint: complaintSlice.reducer
  }
});
