from typing import Any, Optional, Tuple


def has_contraindication(category: Optional[str], answers: dict[str, Any]) -> Tuple[bool, Optional[str]]:
    normalized_category = (category or "").lower()

    if "irm" in normalized_category:
        if answers.get("pacemaker"):
            return True, "Pacemaker declared for an MRI"
        if answers.get("ferromagnetic_implant"):
            return True, "Ferromagnetic implant declared for an MRI"

    if "scanner" in normalized_category and answers.get("with_injection"):
        if answers.get("iodine_allergy"):
            return True, "Iodine allergy declared for an injected scanner"
        if answers.get("renal_failure"):
            return True, "Renal failure declared for an injected scanner"

    if "radio" in normalized_category or "radiographie" in normalized_category:
        if answers.get("pregnant"):
            return True, "Pregnancy declared for an X-ray"

    return False, None
