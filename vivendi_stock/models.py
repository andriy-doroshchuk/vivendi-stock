"""Pydantic models for data validation."""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator


class StockPrice(BaseModel):
    """Validated stock price data point."""

    date: str
    symbol: str
    price: float = Field(..., gt=0, description="Price must be positive")

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError as exc:
            raise ValueError('Date must be in ISO format') from exc

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError('Symbol must be a non-empty string')
        return v.upper()


class ExchangeRate(BaseModel):
    """Validated exchange rate data point."""

    date: str
    currency_pair: str
    rate: float = Field(..., gt=0, description="Rate must be positive")

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError as exc:
            raise ValueError('Date must be in ISO format') from exc

    @field_validator('currency_pair')
    @classmethod
    def validate_currency_format(cls, v: str) -> str:
        if '.' not in v:
            raise ValueError('Currency pair must contain a dot (e.g., EUR.AUD)')
        parts = v.split('.')
        if len(parts) != 2 or len(parts[0]) != 3 or len(parts[1]) != 3:
            raise ValueError('Invalid currency pair format')
        return v.upper()


class APIResponse(BaseModel):
    """Base model for API responses."""

    success: bool
    data: dict | None = None
    error: str | None = None

    @model_validator(mode='after')
    def validate_error_consistency(self):
        if not self.success and not self.error:
            raise ValueError('Error message required when success is False')
        if self.success and self.error:
            raise ValueError('Error message should not be set when success is True')
        return self
