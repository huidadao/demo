"""Transaction log data models."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    """
    Data model for a transaction log entry.
    
    Uses Pydantic for validation and serialization.
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    method: str = Field(..., description="HTTP method (GET, POST, PUT, DELETE, etc.)")
    path: str = Field(..., description="Request path")
    status_code: int = Field(..., description="HTTP response status code")
    duration_ms: float = Field(..., description="Request processing time in milliseconds")
    client_ip: str = Field(default="unknown", description="Client IP address")
    user_agent: Optional[str] = Field(default=None, description="Client user agent string")
    user_id: Optional[int] = Field(default=None, description="Authenticated user ID if available")
    request_body: Optional[Dict[str, Any]] = Field(default=None, description="Request body (sensitive fields masked)")
    response_size: Optional[int] = Field(default=None, description="Response body size in bytes")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
