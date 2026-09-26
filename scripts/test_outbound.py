import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from twilio.rest import Client  # noqa: E402

from app.config import get_settings  # noqa: E402

SAY = "Constancia test call. Geographic permissions are fine."
TWIML = f"<Response><Say language='en-US'>{SAY}</Say></Response>"


def main() -> None:
    settings = get_settings()
    # ponytail: the argument still wins, but with none it resolves DEMO_PHONE the way `make call`
    # already does. Reading it out of .env at the shell is what a documented grep trap eats.
    to = sys.argv[1] if len(sys.argv) > 1 else settings.demo_phone
    if not to:
        raise SystemExit("usage: python scripts/test_outbound.py +54911... (or set DEMO_PHONE)")
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    call = client.calls.create(
        to=to,
        from_=settings.twilio_number,
        twiml=TWIML,
    )
    print(f"call created: {call.sid} -> ...{to[-4:]}")


if __name__ == "__main__":
    main()
