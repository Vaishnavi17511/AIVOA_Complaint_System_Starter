import json
from groq import Groq
from .config import settings

client = Groq(api_key=settings.groq_api_key)

def ask_json(system_prompt: str, user_prompt: str) -> dict:
    response = client.chat.completions.create(
        model=settings.groq_model,
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)
