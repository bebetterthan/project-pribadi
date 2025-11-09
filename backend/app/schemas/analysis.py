from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AIAnalysisResponse(BaseModel):
    id: str
    scan_id: str
    model_used: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    prompt_text: Optional[str] = None  # Full prompt for transparency
    analysis_text: str
    created_at: datetime

    class Config:
        from_attributes = True
