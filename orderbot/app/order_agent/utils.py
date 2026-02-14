from typing import Any, Optional

from google import genai

from app import PROJECT_ROOT

client = genai.Client()


def merge_user(
    left: Optional[dict[str, Any]], right: Optional[dict[str, Any]]
) -> dict[str, Any]:
    """Reducer to merge user state updates."""
    if left is None:
        return right or {}
    if right is None:
        return left
    return {**left, **right}


def generate_weather_image(city: str, weather: str):
    prompt = f"Create a picture of the city of {city} with the weather {weather}"
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt],
    )

    for part in response.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            image = part.as_image()
            image.save(f"{PROJECT_ROOT}/public/weather_image.png")
