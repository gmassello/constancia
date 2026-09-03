import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from twilio.rest import Client  # noqa: E402

from app.config import get_settings  # noqa: E402

SAY = "Prueba de constancia. Permisos geograficos ok."
TWIML = f"<Response><Say language='es-MX'>{SAY}</Say></Response>"


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: python scripts/test_outbound.py +54911...")
    settings = get_settings()
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    call = client.calls.create(
        to=sys.argv[1],
        from_=settings.twilio_number,
        twiml=TWIML,
    )
    print(f"call created: {call.sid} -> {sys.argv[1]}")


if __name__ == "__main__":
    main()
