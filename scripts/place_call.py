import os
import sys

import httpx

BASE = os.environ.get("CONSTANCIA_URL", "http://localhost:8000")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: python scripts/place_call.py +54911...")
    payload = {
        "patient_name": os.environ.get("PATIENT", "Ana"),
        "phone": sys.argv[1],
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
