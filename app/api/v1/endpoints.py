from fastapi import APIRouter

from app.models.v1.recommendation import (
    RecommendationByMenteeRequest,
    RecommendationResponse,
)
from app.services.json_storage import get_mentee_by_id, load_mentors
from app.services.prompt_builder import build_yandex_gpt_recommendation_prompt
from app.services.yandex_gpt_service import YandexGPTService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post(
    "/yandex-gpt/from-json",
    response_model=RecommendationResponse,
)
async def recommend_from_json_files(
    request: RecommendationByMenteeRequest,
) -> RecommendationResponse:
    mentee = get_mentee_by_id(request.mentee_id)
    mentors = load_mentors()

    prompt = build_yandex_gpt_recommendation_prompt(
        mentee=mentee,
        mentors=mentors,
        top_n=request.top_n,
    )

    service = YandexGPTService()
    return await service.get_recommendations(prompt)