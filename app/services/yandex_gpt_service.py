import json
import re

from fastapi import HTTPException
from openai import OpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.models.v1.recommendation import RecommendationResponse


class YandexGPTService:
    def __init__(self) -> None:
        self.client = OpenAI(
            api_key=settings.yandex_cloud_api_key,
            base_url=settings.yandex_cloud_base_url,
            project=settings.yandex_cloud_folder,
        )

        self.model_uri = (
            f"gpt://{settings.yandex_cloud_folder}/"
            f"{settings.yandex_cloud_model}"
        )

    async def get_recommendations(self, prompt: str) -> RecommendationResponse:
        try:
            response = self.client.responses.create(
                model=self.model_uri,
                temperature=0.1,
                instructions=(
                    "Верни только валидный JSON. "
                    "Не используй markdown. "
                    "Не оборачивай ответ в ```json или ```."
                    "Не добавляй текст вне JSON. "
                    "Все строки должны быть на русском языке."
                ),
                input=prompt,
                max_output_tokens=5000,
            )

        except Exception as error:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Ошибка при запросе к YandexGPT через OpenAI-compatible API",
                    "error": str(error),
                },
            ) from error

        response_dict = response.model_dump()
        text_result = self._extract_text_from_response(response)

        if not text_result:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "YandexGPT вернул пустой текст",
                    "raw_response": response_dict,
                },
            )

        cleaned_text = self._clean_json_text(text_result)

        try:
            parsed_result = json.loads(cleaned_text)

            parsed_result["raw_model_response"] = {
                "id": getattr(response, "id", None),
                "model": getattr(response, "model", None),
                "raw_output_text": text_result,
                "cleaned_output_text": cleaned_text,
            }

            return RecommendationResponse(**parsed_result)

        except json.JSONDecodeError as error:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "YandexGPT вернул невалидный JSON после очистки",
                    "raw_output_text": text_result,
                    "cleaned_output_text": cleaned_text,
                    "json_error": str(error),
                },
            ) from error

        except ValidationError as error:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "JSON от YandexGPT не соответствует RecommendationResponse",
                    "validation_errors": error.errors(),
                    "raw_output_text": text_result,
                    "cleaned_output_text": cleaned_text,
                },
            ) from error

    @staticmethod
    def _extract_text_from_response(response) -> str:
        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text.strip()

        parts: list[str] = []

        for item in getattr(response, "output", []) or []:
            content = getattr(item, "content", None) or []

            for content_item in content:
                text = getattr(content_item, "text", None)
                if text:
                    parts.append(text)

        return "\n".join(parts).strip()

    @staticmethod
    def _clean_json_text(text: str) -> str:
        text = text.strip()

        # Убираем markdown-блоки вида ```json ... ``` или ``` ... ```
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)

        # Если модель все равно добавила текст до/после JSON, вырезаем первый JSON-объект
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]

        return text.strip()