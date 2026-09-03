import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google import genai  # noqa: E402

from app.config import get_settings  # noqa: E402


def main() -> None:
    client = genai.Client(api_key=get_settings().gemini_api_key)
    for model in client.models.list():
        print(model.name)


if __name__ == "__main__":
    main()
