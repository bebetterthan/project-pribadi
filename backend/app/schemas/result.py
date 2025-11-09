from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class ScanResultResponse(BaseModel):
    id: str
    scan_id: str
    tool_name: str
    raw_output: str
    parsed_output: Optional[Dict[str, Any]]
    exit_code: int
    execution_time: float
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
