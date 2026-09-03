from urllib.parse import urljoin

from fastapi import HTTPException, Request
from starlette.datastructures import FormData
from twilio.request_validator import RequestValidator

from app.config import get_settings


def signed_url(request: Request) -> str:
    settings = get_settings()
    url = urljoin(settings.public_base_url, request.url.path)
    return f"{url}?{request.url.query}" if request.url.query else url


async def twilio_form(request: Request) -> FormData:
    form = await request.form()
    settings = get_settings()
    if settings.validate_twilio_signature:
        signature = request.headers.get("X-Twilio-Signature", "")
        validator = RequestValidator(settings.twilio_auth_token)
        if not validator.validate(signed_url(request), dict(form), signature):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    return form
