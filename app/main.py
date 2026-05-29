from datetime import date, datetime, timedelta
from typing import Any, Optional
import json
import re
import unicodedata

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import ENOVACOM_SITE_ID
from app.enovacom import EnovacomError, client
from app.gemini import resolve_exam_ambiguity, structure_booking_request
from app.rules import has_contraindication

app = FastAPI(title="Rounded radiology tools")


class SearchExamRequest(BaseModel):
    query: str
    clarification_answer: Optional[str] = None


class FindPatientRequest(BaseModel):
    phone_number: str
    last_name: Optional[str] = None


class AvailableSlotsRequest(BaseModel):
    visit_motive_id: str
    start_date: str
    days: int = 14


class Slot(BaseModel):
    start: str
    duration_minutes: str
    practitioner_id: str
    location_id: Optional[str] = None
    site_id: Optional[str] = None


class Patient(BaseModel):
    first_name: str
    last_name: str
    birth_date: str
    gender: str = "1"
    phone: str


class CreateAppointmentRequest(BaseModel):
    visit_motive_id: str
    slot: Optional[Slot] = None
    patient_id: str = "0"
    patient: Optional[Patient] = None
    contraindications: dict[str, Any] = Field(default_factory=dict)
    exam_category: Optional[str] = None
    start: Optional[str] = None
    duration_minutes: Optional[str] = None
    practitioner_id: Optional[str] = None
    location_id: Optional[str] = None
    site_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[str] = None
    gender: str = "1"
    phone: Optional[str] = None
    pacemaker: Optional[bool] = None
    ferromagnetic_implant: Optional[bool] = None
    pregnant: Optional[bool] = None
    iodine_allergy: Optional[bool] = None
    renal_failure: Optional[bool] = None


class CancelAppointmentRequest(BaseModel):
    appointment_id: str


class CreateAppointmentFromTextRequest(BaseModel):
    request_text: str


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def normalize_date_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_accents.replace("'", " ")).strip()


def get_value(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in item:
            return item[key]
    return None


def get_category_name(config: dict[str, Any], category_id: Any) -> Optional[str]:
    for category in config.get("categories", []):
        current_id = get_value(category, "id", "category_id", "id_category")
        if str(current_id) == str(category_id):
            return get_value(category, "name", "label", "category_name")
    return None


def allowed_visit_motive_ids(config: dict[str, Any]) -> Optional[set[str]]:
    if not ENOVACOM_SITE_ID:
        return None

    allowed: set[str] = set()
    for link in config.get("links", []):
        site_id = get_value(link, "site_id", "id_site")
        motive_id = get_value(link, "visit_motive_id", "id_visit_motive", "id_examen")
        if str(site_id) == str(ENOVACOM_SITE_ID) and motive_id is not None:
            allowed.add(str(motive_id))

    return allowed


def parse_api_date(value: str) -> Optional[datetime]:
    for date_format in ("%Y-%m-%d %H:%M:%S", "%Y%m%dT%H:%M:%S.000Z", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue
    return None


def parse_start_date(value: str) -> date:
    text = normalize_date_text(value)
    today = date.today()

    relative_dates = {
        "aujourd hui": today,
        "aujourdhui": today,
        "today": today,
        "demain": today + timedelta(days=1),
        "tomorrow": today + timedelta(days=1),
        "apres demain": today + timedelta(days=2),
        "apres-demain": today + timedelta(days=2),
    }
    if text in relative_dates:
        return relative_dates[text]

    days_match = re.search(r"dans (\d+) jours?", text)
    if days_match:
        return today + timedelta(days=int(days_match.group(1)))

    weekday_indexes = {
        "lundi": 0,
        "mardi": 1,
        "mercredi": 2,
        "jeudi": 3,
        "vendredi": 4,
        "samedi": 5,
        "dimanche": 6,
    }
    for weekday_name, weekday_index in weekday_indexes.items():
        if weekday_name in text:
            delta = (weekday_index - today.weekday()) % 7
            if "prochain" in text and delta == 0:
                delta = 7
            return today + timedelta(days=delta)

    month_indexes = {
        "janvier": 1,
        "fevrier": 2,
        "mars": 3,
        "avril": 4,
        "mai": 5,
        "juin": 6,
        "juillet": 7,
        "aout": 8,
        "septembre": 9,
        "octobre": 10,
        "novembre": 11,
        "decembre": 12,
    }
    month_pattern = r"(\d{1,2})\s+(" + "|".join(month_indexes.keys()) + r")(?:\s+(\d{4}))?"
    month_match = re.search(month_pattern, text)
    if month_match:
        day = int(month_match.group(1))
        month = month_indexes[month_match.group(2)]
        year = int(month_match.group(3) or today.year)
        parsed = date(year, month, day)
        if not month_match.group(3) and parsed < today:
            parsed = date(year + 1, month, day)
        return parsed

    date_formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%d/%m/%y",
        "%d-%m-%y",
        "%Y%m%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%fZ",
    ]
    for date_format in date_formats:
        try:
            return datetime.strptime(value.strip(), date_format).date()
        except ValueError:
            continue

    short_date_match = re.search(r"\b(\d{1,2})[/-](\d{1,2})\b", text)
    if short_date_match:
        day = int(short_date_match.group(1))
        month = int(short_date_match.group(2))
        parsed = date(today.year, month, day)
        if parsed < today:
            parsed = date(today.year + 1, month, day)
        return parsed

    raise ValueError(
        "start_date must be a date like YYYY-MM-DD, DD/MM/YYYY, 'demain', 'apres-demain', a French weekday, or '28 mai 2026'"
    )


def summarize_exam_matches(matches: list[dict[str, Any]]) -> str:
    if not matches:
        return "Aucun examen correspondant n'a ete trouve. Demander une precision ou transferer a un humain."

    names = [f"{item['name']} (id {item['visit_motive_id']})" for item in matches[:3]]
    return "Examens trouves : " + "; ".join(names) + ". Si plusieurs options sont possibles, demander une precision au patient."


def selected_exam_response(selected_exam: dict[str, Any], matches: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "selected",
        "selected_exam": selected_exam,
        "matches": matches,
        "instructions": "Utiliser selected_exam.visit_motive_id pour chercher les creneaux avec get_available_slots.",
    }


def no_match_exam_response() -> dict[str, Any]:
    return {
        "status": "no_match",
        "matches": [],
        "instructions": "Demander une precision simple ou transferer a un humain.",
    }


def clarification_exam_response(
    matches: list[dict[str, Any]],
    question: str = "Pouvez-vous preciser l'examen souhaite ?",
) -> dict[str, Any]:
    return {
        "status": "needs_clarification",
        "clarification_question": question,
        "matches": matches,
        "instructions": "Poser clarification_question au patient, puis rappeler search_exam avec query et clarification_answer.",
    }


def apply_exam_resolution(
    query: str,
    matches: list[dict[str, Any]],
    clarification_answer: Optional[str],
) -> dict[str, Any]:
    try:
        resolution = resolve_exam_ambiguity(query, matches, clarification_answer)
    except (EnovacomError, RuntimeError, json.JSONDecodeError):
        return clarification_exam_response(matches)

    status = resolution.get("status")
    selected_id = str(resolution.get("selected_visit_motive_id") or "")

    if status == "selected" and selected_id:
        for match in matches:
            if str(match.get("visit_motive_id")) == selected_id:
                return selected_exam_response(match, matches)

    if status == "no_match":
        return no_match_exam_response()

    question = resolution.get("clarification_question") or "Pouvez-vous preciser l'examen souhaite ?"
    return clarification_exam_response(matches, str(question))


def summarize_slots(slots: list[dict[str, Any]]) -> str:
    if not slots:
        return "Aucun creneau disponible sur cette periode. Proposer une autre periode ou transferer a un humain."

    options = [f"{slot['start']} (praticien {slot['practitioner_id']})" for slot in slots[:3]]
    return "Proposer ces creneaux au patient : " + "; ".join(options) + ". Ne creer le rendez-vous qu'apres confirmation explicite."


def normalize_birth_date(value: str) -> str:
    text = value.strip()
    for date_format in ("%Y%m%d", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(text, date_format).strftime("%Y%m%d")
        except ValueError:
            continue
    return text


def build_slot(payload: CreateAppointmentRequest) -> Slot:
    if payload.slot:
        return payload.slot

    missing = [
        name
        for name, value in {
            "start": payload.start,
            "duration_minutes": payload.duration_minutes,
            "practitioner_id": payload.practitioner_id,
        }.items()
        if not value
    ]
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing slot fields: {', '.join(missing)}")

    return Slot(
        start=payload.start or "",
        duration_minutes=str(payload.duration_minutes),
        practitioner_id=str(payload.practitioner_id),
        location_id=payload.location_id,
        site_id=payload.site_id,
    )


def build_patient(payload: CreateAppointmentRequest) -> Patient:
    if payload.patient:
        return payload.patient

    missing = [
        name
        for name, value in {
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "birth_date": payload.birth_date,
            "phone": payload.phone,
        }.items()
        if not value
    ]
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing patient fields: {', '.join(missing)}")

    return Patient(
        first_name=payload.first_name or "",
        last_name=payload.last_name or "",
        birth_date=normalize_birth_date(payload.birth_date or ""),
        gender=payload.gender,
        phone=payload.phone or "",
    )


def build_contraindications(payload: CreateAppointmentRequest) -> dict[str, Any]:
    answers = dict(payload.contraindications)
    for field in ["pacemaker", "ferromagnetic_implant", "pregnant", "iodine_allergy", "renal_failure"]:
        value = getattr(payload, field)
        if value is not None:
            answers[field] = value
    return answers


def model_to_dict(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def missing_booking_fields(data: dict[str, Any]) -> list[str]:
    required = [
        "visit_motive_id",
        "start",
        "duration_minutes",
        "practitioner_id",
        "location_id",
        "first_name",
        "last_name",
        "birth_date",
        "phone",
        "exam_category",
    ]
    return [field for field in required if not data.get(field)]


def call_enovacom(command: str, **params: Any) -> dict[str, Any]:
    try:
        return client.call(command, **params)
    except (EnovacomError, RuntimeError) as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


def get_enovacom_config() -> dict[str, Any]:
    try:
        return client.get_config()
    except (EnovacomError, RuntimeError) as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/tools/search_exam")
def search_exam(payload: SearchExamRequest) -> dict[str, Any]:
    config = get_enovacom_config()
    allowed_ids = allowed_visit_motive_ids(config)
    query_words = normalize(payload.query).split()

    matches: list[dict[str, Any]] = []
    for motive in config.get("visit_motives", []):
        motive_id = get_value(motive, "id", "visit_motive_id", "id_examen")
        if allowed_ids is not None and str(motive_id) not in allowed_ids:
            continue

        name = get_value(motive, "name", "label", "libelle")
        if not name:
            continue

        normalized_name = normalize(str(name))
        if all(word in normalized_name for word in query_words):
            category_id = get_value(motive, "category_id", "id_category")
            matches.append(
                {
                    "visit_motive_id": str(motive_id),
                    "name": name,
                    "category": get_category_name(config, category_id),
                }
            )

    selected_matches = matches[:5]
    if not selected_matches:
        return no_match_exam_response()

    if len(selected_matches) == 1:
        return selected_exam_response(selected_matches[0], selected_matches)

    return apply_exam_resolution(payload.query, selected_matches, payload.clarification_answer)


@app.post("/tools/find_patient")
def find_patient(payload: FindPatientRequest) -> dict[str, Any]:
    params = {"phone_number": payload.phone_number}
    if payload.last_name:
        params["last_name"] = payload.last_name

    response = call_enovacom("get_patient", **params)

    patients = response.get("patients") or response.get("patient") or []
    if isinstance(patients, dict):
        patients = [patients]

    return {
        "found": len(patients) == 1,
        "ambiguous": len(patients) > 1,
        "patients": patients,
        "instructions": (
            "Patient unique trouve : confirmer son identite avant de continuer."
            if len(patients) == 1
            else "Plusieurs patients possibles : demander une verification supplementaire ou transferer a un humain."
            if len(patients) > 1
            else "Aucun patient trouve : collecter les informations patient necessaires."
        ),
    }


@app.post("/tools/get_available_slots")
def get_available_slots(payload: AvailableSlotsRequest) -> dict[str, Any]:
    try:
        start_day = parse_start_date(payload.start_date)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    start = datetime.combine(start_day, datetime.min.time())
    stop = start + timedelta(days=payload.days)

    response = call_enovacom(
        "get_availabilities",
        visit_motive_id=int(payload.visit_motive_id),
        start_date=start.strftime("%Y%m%dT00:00:00.000Z"),
        stop_date=stop.strftime("%Y%m%dT23:59:59.000Z"),
    )

    slots: list[dict[str, Any]] = []
    for item in response.get("availabilities", []):
        site_id = get_value(item, "site_id", "id_site")
        if ENOVACOM_SITE_ID and str(site_id) != str(ENOVACOM_SITE_ID):
            continue

        start_date = get_value(item, "start_date", "start")
        stop_date = get_value(item, "stop_date", "end", "stop")
        start_dt = parse_api_date(str(start_date)) if start_date else None
        stop_dt = parse_api_date(str(stop_date)) if stop_date else None
        duration = "0"
        if start_dt and stop_dt:
            duration = str(int((stop_dt - start_dt).total_seconds() / 60))

        slots.append(
            {
                "start": start_dt.strftime("%Y-%m-%d %H:%M:%S") if start_dt else start_date,
                "stop": stop_dt.strftime("%Y-%m-%d %H:%M:%S") if stop_dt else stop_date,
                "duration_minutes": duration,
                "practitioner_id": str(get_value(item, "practitioner_id", "id_ps")),
                "location_id": str(get_value(item, "location_id", "id_location")),
                "site_id": str(site_id),
            }
        )

    selected_slots = slots[:10]
    return {
        "slots": selected_slots,
        "instructions": summarize_slots(selected_slots),
    }


@app.post("/tools/create_appointment")
def create_appointment(payload: CreateAppointmentRequest) -> dict[str, Any]:
    slot = build_slot(payload)
    patient = build_patient(payload)
    contraindications = build_contraindications(payload)

    blocked, reason = has_contraindication(payload.exam_category, contraindications)
    if blocked:
        return {
            "appointment_created": False,
            "reason": reason,
            "next_action": "transfer",
            "instructions": "Ne pas creer le rendez-vous. Informer le patient que sa situation doit etre verifiee par l'equipe du centre et transferer a un humain.",
        }

    response = call_enovacom(
        "add_rdv",
        visit_motive_id=payload.visit_motive_id,
        id_examen=payload.visit_motive_id,
        rdv_datetime=slot.start,
        rdv_duration_minute=slot.duration_minutes,
        id_vacation="0",
        id_ps=slot.practitioner_id,
        patient_id=payload.patient_id,
        sending_application="rounded",
        patient=model_to_dict(patient),
    )

    return {
        "appointment_created": bool(response.get("appointment_created")),
        "appointment_id": response.get("appointment_id"),
        "instructions": "Le rendez-vous est cree. Recapituler l'examen, la date, l'heure et rappeler que l'agent ne donne pas d'information medicale.",
        "raw": response,
    }


@app.post("/tools/create_appointment_from_text")
def create_appointment_from_text(payload: CreateAppointmentFromTextRequest) -> dict[str, Any]:
    try:
        structured = structure_booking_request(payload.request_text)
    except (EnovacomError, RuntimeError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    missing = missing_booking_fields(structured)
    if missing:
        return {
            "appointment_created": False,
            "missing_fields": missing,
            "structured": structured,
            "instructions": "Il manque des informations pour creer le rendez-vous. Demander ces informations au patient puis rappeler le tool.",
        }

    normalized_payload = CreateAppointmentRequest(**structured)
    result = create_appointment(normalized_payload)
    result["structured"] = structured
    return result


@app.post("/tools/cancel_appointment")
def cancel_appointment(payload: CancelAppointmentRequest) -> dict[str, Any]:
    response = call_enovacom(
        "delete_rdv",
        id_rdv=payload.appointment_id,
        sending_application="rounded",
    )

    return {
        "cancelled": bool(
            response.get("appointment_deleted")
            or response.get("appointement_deleted")
            or response.get("deleted")
            or response.get("success")
        ),
        "instructions": "Si cancelled=true, confirmer au patient que le rendez-vous est annule. Sinon, transferer a un humain.",
        "raw": response,
    }
