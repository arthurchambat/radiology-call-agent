from datetime import datetime, timedelta
from typing import Any, Optional
import re

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import ENOVACOM_SITE_ID
from app.enovacom import EnovacomError, client
from app.rules import has_contraindication

app = FastAPI(title="Rounded radiology tools")


class SearchExamRequest(BaseModel):
    query: str


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
    slot: Slot
    patient_id: str = "0"
    patient: Patient
    contraindications: dict[str, Any] = Field(default_factory=dict)
    exam_category: Optional[str] = None


class CancelAppointmentRequest(BaseModel):
    appointment_id: str


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


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

    return {"matches": matches[:5]}


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
    }


@app.post("/tools/get_available_slots")
def get_available_slots(payload: AvailableSlotsRequest) -> dict[str, Any]:
    start = datetime.strptime(payload.start_date, "%Y-%m-%d")
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

    return {"slots": slots[:10]}


@app.post("/tools/create_appointment")
def create_appointment(payload: CreateAppointmentRequest) -> dict[str, Any]:
    blocked, reason = has_contraindication(payload.exam_category, payload.contraindications)
    if blocked:
        return {
            "appointment_created": False,
            "reason": reason,
            "next_action": "transfer",
        }

    response = call_enovacom(
        "add_rdv",
        visit_motive_id=payload.visit_motive_id,
        id_examen=payload.visit_motive_id,
        rdv_datetime=payload.slot.start,
        rdv_duration_minute=payload.slot.duration_minutes,
        id_vacation="0",
        id_ps=payload.slot.practitioner_id,
        patient_id=payload.patient_id,
        sending_application="rounded",
        patient=payload.patient.dict(),
    )

    return {
        "appointment_created": bool(response.get("appointment_created")),
        "appointment_id": response.get("appointment_id"),
        "raw": response,
    }


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
        "raw": response,
    }
