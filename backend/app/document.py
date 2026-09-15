from pathlib import Path
from email import policy
from email.parser import BytesParser
from io import BytesIO
from pypdf import PdfReader

def extract_text(filename: str, data: bytes) -> str:
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        reader = PdfReader(BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if ext == ".txt":
        return data.decode("utf-8", errors="ignore")

    if ext == ".eml":
        msg = BytesParser(policy=policy.default).parsebytes(data)
        body = msg.get_body(preferencelist=("plain", "html"))
        return "\n".join([
            f"Subject: {msg.get('subject', '')}",
            f"From: {msg.get('from', '')}",
            body.get_content() if body else ""
        ])

    raise ValueError("Supported formats: PDF, TXT, EML")
