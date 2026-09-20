import os
import sys

import httpx

BASE = os.environ.get("CONSTANCIA_URL", "http://localhost:8001")
ANA = "8c9d0e1f-2a3b-4c5d-6e7f-8091a2b3c4d5"


def main() -> None:
    payload = {
        "patient_id": os.environ.get("PATIENT_ID", ANA),
        "phone": sys.argv[1] if len(sys.argv) > 1 else None,
        "pack": os.environ.get("PACK", "rehab"),
        "memory": os.environ.get("MEMORY", "on") != "off",
    }
    response = httpx.post(f"{BASE}/calls", json=payload, timeout=30)
    response.raise_for_status()
    body = response.json()
    print(body)
    print(f"trace: {BASE}/calls/{body['call_id']}/trace")


if __name__ == "__main__":
    main()
