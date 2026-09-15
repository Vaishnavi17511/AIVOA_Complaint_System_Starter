# AIVOA - AI-Powered Customer Complaint Management System

This is a starter implementation for the internship challenge.

Architecture:
React + Redux Toolkit
        |
        v
FastAPI
        |
        v
LangGraph workflow
        |
        v
Groq LLM
        |
        v
PostgreSQL

Implemented:
- Natural-language complaint creation
- Natural-language complaint correction/update
- PDF/TXT/EML text extraction
- AI risk assessment
- PostgreSQL save
- React + Redux frontend
- LangGraph backend workflow

Backend:
1. Create a PostgreSQL database named `aivoa_qms`.
2. Open a terminal in `backend`.
3. Create and activate a Python virtual environment.
4. `pip install -r requirements.txt`
5. Copy `.env.example` to `.env`.
6. Add your Groq API key.
7. Run `uvicorn app.main:app --reload`

Frontend:
1. Open a second terminal in `frontend`.
2. Run `npm install`
3. Run `npm run dev`
4. Open http://localhost:5173

Demo prompt:
Apollo Pharmacy reported discolored Amoxicillin capsules 500 mg. The complaint concerns a product quality issue.

Then test:
Sorry, the batch number is BMX240602 and affected quantity is 48 capsules.

Important:
The assignment asks for `gemma2-9b-it`, but Groq's current documentation lists that model as deprecated. Keep the model configurable in `.env` and use the assignment model only if it is actually available to your Groq account; otherwise use the current supported replacement and explain this clearly during the interview.
