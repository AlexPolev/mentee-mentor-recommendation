from typing import Any, Optional

from pydantic import BaseModel, Field


class RecommendationByMenteeRequest(BaseModel):
    mentee_id: str = Field(..., description="ID конкретного менти из mentees.json")
    top_n: int = Field(default=5, ge=1, le=20)


class RecommendedMentor(BaseModel):
    mentor_id: str
    mentor_name: str
    rank: int
    score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Оценка релевантности, если YandexGPT решил ее использовать",
    )
    explanation: str = Field(
        ...,
        description="Почему YandexGPT рекомендует именно этого ментора",
    )
    matched_factors: list[str] = Field(
        default_factory=list,
        description="Какие факторы совпали",
    )
    possible_risks: list[str] = Field(
        default_factory=list,
        description="Какие есть ограничения или риски рекомендации",
    )


class RecommendationResponse(BaseModel):
    mentee_id: str
    recommendation_logic: str = Field(
        ...,
        description="Как YandexGPT сам решил подбирать менторов",
    )
    recommendations: list[RecommendedMentor]
    general_explanation: str
    raw_model_response: Optional[dict[str, Any]] = None