from fastapi import APIRouter, Request

from app.domain.onboarding import OnboardingRequest, OnboardingResult

router = APIRouter(prefix="/api/v1")


@router.post("/onboarding/start", response_model=OnboardingResult)
async def start_onboarding(body: OnboardingRequest, request: Request) -> OnboardingResult:
    return await request.app.state.start_onboarding.execute(body)


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}
