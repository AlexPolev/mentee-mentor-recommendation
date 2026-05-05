import json

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.models.v1.recommendation import RecommendationResponse


class YandexGPTService:
    def __init__(self) -> None:
        self.url = settings.yandex_gpt_url
        self.api_key = settings.yandex_gpt_api_key
        self.folder_id = settings.yandex_gpt_folder_id
        self.model = settings.yandex_gpt_model

    async def get_recommendations(self, prompt: str) -> RecommendationResponse:
        payload = {
            "modelUri": f"gpt://{self.folder_id}/{self.model}/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.2,
                "maxTokens": "3000",
            },
            "messages": [
                {
                    "role": "system",
                    "text": (
                        "Ты возвращаешь только валидный JSON. "
                        "Нельзя использовать markdown. "
                        "Нельзя писать текст вне JSON."
                    ),
                },
                {
                    "role": "user",
                    "text": prompt,
                },
            ],
            "jsonObject": True,
        }

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=90) as client:
                response = await client.post(
                    self.url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()

        except httpx.HTTPStatusError as error:
            raise HTTPException(
                status_code=error.response.status_code,
                detail={
                    "message": "YandexGPT API вернул ошибку",
                    "response": error.response.text,
                },
            ) from error

        except httpx.RequestError as error:
            raise HTTPException(
                status_code=502,
                detail=f"Ошибка соединения с YandexGPT API: {str(error)}",
            ) from error

        data = response.json()

        try:
            text_result = data["alternatives"][0]["message"]["text"]
            parsed_result = json.loads(text_result)
            parsed_result["raw_model_response"] = data

            return RecommendationResponse(**parsed_result)

        except (KeyError, IndexError, json.JSONDecodeError, TypeError, ValueError) as error:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Не удалось привести ответ YandexGPT к ожидаемой структуре",
                    "raw_response": data,
                },
            ) from error