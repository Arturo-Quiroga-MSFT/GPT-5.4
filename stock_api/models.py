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
