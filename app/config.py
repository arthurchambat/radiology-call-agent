import os
from pathlib import Path


def load_local_env() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_local_env()


ENOVACOM_BASE_URL = os.getenv(
    "ENOVACOM_BASE_URL",
    "https://ris-recette-instance3.nd.care/AIR/eris_project/eris_php/WebServices/WS_rdv_externe.php",
)
ENOVACOM_TOKEN = os.getenv("ENOVACOM_TOKEN")
ENOVACOM_SITE_ID = os.getenv("ENOVACOM_SITE_ID")


def require_token() -> str:
    if not ENOVACOM_TOKEN:
        raise RuntimeError("ENOVACOM_TOKEN is missing")
    return ENOVACOM_TOKEN
