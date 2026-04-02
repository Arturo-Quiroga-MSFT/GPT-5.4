"""
Pydantic request / response schemas for the Stock Analysis API.
"""

import re
from pydantic import BaseModel, Field, field_validator


class AnalyseRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol, e.g. AAPL")
    days: int = Field(..., ge=1, le=365, description="Number of calendar days to look back")

    @field_validator("ticker")
    @classmethod
    def normalise_ticker(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r"^[A-Z0-9.\-]+$", v):
            raise ValueError("Ticker must contain only letters, digits, '.', or '-'")
        return v


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Free-form user message")
    previous_response_id: str | None = Field(default=None, description="Response ID from the previous turn for conversation chaining")

    @field_validator("message")
    @classmethod
    def clean_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        return v


REASONING_LEVELS = {"low", "medium", "high"}


class CompareRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Query to run at all reasoning levels")
    levels: list[str] = Field(default=["low", "medium", "high"], description="Reasoning effort levels to compare")

    @field_validator("message")
    @classmethod
    def clean_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        return v

    @field_validator("levels")
    @classmethod
    def validate_levels(cls, v: list[str]) -> list[str]:
        for level in v:
            if level not in REASONING_LEVELS:
                raise ValueError(f"Invalid level '{level}'. Must be one of: {REASONING_LEVELS}")
        return v


class JudgeRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="The original question asked")
    low_response: str = Field(..., min_length=1, description="Response from the low reasoning level")
    medium_response: str = Field(..., min_length=1, description="Response from the medium reasoning level")
    high_response: str = Field(..., min_length=1, description="Response from the high reasoning level")


class FomcChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Question about FOMC / monetary policy")
    previous_response_id: str | None = Field(default=None, description="Response ID from the previous turn")

    @field_validator("message")
    @classmethod
    def clean_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        return v
