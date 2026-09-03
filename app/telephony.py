from twilio.rest import Client
from twilio.twiml.voice_response import Connect, VoiceResponse

from app.config import get_settings


def media_url(call_id: str) -> str:
    base = get_settings().public_base_url.rstrip("/")
    host = base.split("://", 1)[-1]
    return f"wss://{host}/media/{call_id}"


def stream_twiml(call_id: str) -> str:
    response = VoiceResponse()
    connect = Connect()
    connect.stream(url=media_url(call_id))
    response.append(connect)
    return str(response)


def place_call(call_id: str, to: str) -> str:
    settings = get_settings()
    base = settings.public_base_url.rstrip("/")
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    call = client.calls.create(
        to=to,
        from_=settings.twilio_number,
        url=f"{base}/voice?call_id={call_id}",
        status_callback=f"{base}/voice/status",
        record=True,
        recording_status_callback=f"{base}/voice/recording",
    )
    return call.sid
