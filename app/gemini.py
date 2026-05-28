import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.config import GEMINI_MODEL, require_gemini_key
from app.enovacom import EnovacomError


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()

    start = cleaned.find("{")
    stop = cleaned.rfind("}")
    if start == -1 or stop == -1 or stop <= start:
        raise EnovacomError("Gemini did not return a JSON object")

    return json.loads(cleaned[start : stop + 1])


def structure_booking_request(request_text: str) -> dict[str, Any]:
    api_key = require_gemini_key()
    query = urlencode({"key": api_key})
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?{query}"

    prompt = f"""
Tu extrais les informations d'une demande de rendez-vous de radiologie.
Retourne uniquement un objet JSON valide, sans markdown.

Champs attendus :
- visit_motive_id: string
- start: string au format YYYY-MM-DD HH:MM:SS
- duration_minutes: string
- practitioner_id: string
- location_id: string
- patient_id: string, "0" si nouveau patient
- first_name: string
- last_name: string
- birth_date: string au format YYYYMMDD
- gender: string, "1" par defaut si inconnu
- phone: string
- exam_category: string, par exemple IRM, Scanner, Radio
- pacemaker: boolean
- ferromagnetic_implant: boolean
- pregnant: boolean
- iodine_allergy: boolean
- renal_failure: boolean

Si une valeur manque, mets une chaine vide pour les strings et false pour les booleans.

Demande :
{request_text}
""".strip()

    body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt,
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "response_mime_type": "application/json",
        },
    }

    request = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=20) as response:
        parsed = json.loads(response.read().decode("utf-8"))

    try:
        text = parsed["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as error:
        raise EnovacomError("Gemini returned an unexpected response") from error

    return extract_json_object(text)
