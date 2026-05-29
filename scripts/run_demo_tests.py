import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://radiology-call-agent.vercel.app"


def post_json(base_url: str, path: str, payload: dict) -> dict:
    request = Request(
        f"{base_url}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(base_url: str, path: str) -> dict:
    with urlopen(f"{base_url}{path}", timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def print_step(title: str, data: dict) -> None:
    print(f"\n## {title}")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def run_smoke_tests(base_url: str) -> dict:
    health = get_json(base_url, "/health")
    print_step("health", health)
    assert health["status"] == "ok"

    exams = post_json(base_url, "/tools/search_exam", {"query": "irm genou"})
    print_step("search_exam", exams)
    assert exams["matches"], "No exam found"

    selected_exam = exams.get("selected_exam")
    if exams.get("status") == "needs_clarification":
        clarified = post_json(
            base_url,
            "/tools/search_exam",
            {"query": "irm genou", "clarification_answer": "sans injection"},
        )
        print_step("search_exam_clarified", clarified)
        assert clarified["status"] == "selected"
        selected_exam = clarified["selected_exam"]

    assert selected_exam, "No selected exam found"
    first_exam = selected_exam
    visit_motive_id = first_exam["visit_motive_id"]

    slots = post_json(
        base_url,
        "/tools/get_available_slots",
        {
            "visit_motive_id": visit_motive_id,
            "start_date": "2026-05-28",
            "days": 14,
        },
    )
    print_step("get_available_slots", slots)
    assert slots["slots"], "No slot found"

    blocked = post_json(
        base_url,
        "/tools/create_appointment",
        {
            "visit_motive_id": visit_motive_id,
            "slot": slots["slots"][0],
            "patient_id": "0",
            "patient": {
                "first_name": "Test",
                "last_name": "Blocked",
                "birth_date": "19900101",
                "gender": "1",
                "phone": "0600000001",
            },
            "exam_category": first_exam.get("category") or "IRM",
            "contraindications": {
                "pacemaker": True,
                "ferromagnetic_implant": False,
            },
        },
    )
    print_step("contraindication_refusal", blocked)
    assert blocked["appointment_created"] is False
    assert blocked["next_action"] == "transfer"

    return {
        "visit_motive_id": visit_motive_id,
        "exam_category": first_exam.get("category") or "IRM",
        "slot": slots["slots"][-1],
    }


def run_create_cancel(base_url: str, context: dict) -> None:
    created = post_json(
        base_url,
        "/tools/create_appointment",
        {
            "visit_motive_id": context["visit_motive_id"],
            "slot": context["slot"],
            "patient_id": "0",
            "patient": {
                "first_name": "Test",
                "last_name": "Demo",
                "birth_date": "19900101",
                "gender": "1",
                "phone": "0600000002",
            },
            "exam_category": context["exam_category"],
            "contraindications": {
                "pacemaker": False,
                "ferromagnetic_implant": False,
            },
        },
    )
    print_step("create_appointment", created)
    assert created["appointment_created"] is True

    appointment_id = str(created["appointment_id"])
    cancelled = post_json(
        base_url,
        "/tools/cancel_appointment",
        {"appointment_id": appointment_id},
    )
    print_step("cancel_appointment", cancelled)
    assert cancelled["cancelled"] is True


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the live demo checks.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument(
        "--e2e",
        action="store_true",
        help="Also create and cancel a real appointment in Enovacom recette.",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    print(f"Testing {base_url}")

    try:
        context = run_smoke_tests(base_url)
        if args.e2e:
            run_create_cancel(base_url, context)
    except (AssertionError, HTTPError, URLError, TimeoutError) as error:
        print(f"\nTest failed: {error}")
        raise SystemExit(1)

    print("\nAll requested checks passed.")


if __name__ == "__main__":
    main()
