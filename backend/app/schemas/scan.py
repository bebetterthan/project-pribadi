from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from app.models.scan import ScanStatus


class ScanCreate(BaseModel):
    target: str = Field(..., description="Target domain, IP, or URL")
    user_prompt: Optional[str] = Field(None, description="User's objective/instruction for AI agent")
    tools: Optional[List[str]] = Field(None, description="List of tools to use (if not provided, AI will decide)")
    profile: str = Field("normal", description="Scan profile: quick, normal, or aggressive")
    enable_ai: bool = Field(True, description="Enable AI analysis")

    @validator('tools')
    def validate_tools(cls, v):
        if v is None:
            return v  # AI will decide tools
        valid_tools = ['nmap', 'nuclei', 'whatweb', 'sslscan']
        for tool in v:
            if tool not in valid_tools:
                raise ValueError(f"Invalid tool: {tool}. Valid tools: {valid_tools}")
        return v

    @validator('profile')
    def validate_profile(cls, v):
        valid_profiles = ['quick', 'normal', 'aggressive']
        if v not in valid_profiles:
            raise ValueError(f"Invalid profile: {v}. Valid profiles: {valid_profiles}")
        return v


class ScanResponse(BaseModel):
    id: str
    target: str
    user_prompt: Optional[str]
    ai_strategy: Optional[dict]
    agent_thoughts: Optional[List[dict]]
    tools: List[str]
    profile: str
    status: ScanStatus
    current_tool: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScanListResponse(BaseModel):
    scans: List[ScanResponse]
    total: int
