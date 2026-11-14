"""
NASA Space Apps Challenge 2026 - Earth Systems Trend Detective
AI Assistant Route
"""

from fastapi import APIRouter, HTTPException
from ..schemas import AIQueryRequest, AIQueryResponse
from ..services.ai_service import ai_service
from ..config import GEMINI_API_KEY, GROQ_API_KEY, OPENAI_API_KEY

router = APIRouter(prefix="/api/assistant", tags=["assistant"])

@router.post("/chat", response_model=AIQueryResponse)
def chat_with_assistant(req: AIQueryRequest):
    try:
        res = ai_service.answer_question(
            question=req.question,
            context=req.context,
            provider=req.provider or "auto"
        )
        return AIQueryResponse(
            success=True,
            question=req.question,
            provider_used=res["provider_used"],
            answer=res["answer"],
            grounded_evidence=res["grounded_evidence"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/providers")
def get_providers():
    return {
        "success": True,
        "providers": [
            {"id": "gemini", "name": "Google Gemini 1.5", "configured": bool(GEMINI_API_KEY)},
            {"id": "groq", "name": "Groq LLaMA 3.3 70B", "configured": bool(GROQ_API_KEY)},
            {"id": "openai", "name": "OpenAI GPT-4o", "configured": bool(OPENAI_API_KEY)},
            {"id": "local", "name": "Grounded Scientific Engine (Local Rule-Based)", "configured": True}
        ]
    }
