from pydantic import BaseModel, NonNegativeInt, PositiveInt


class ExpRetryConfig(BaseModel):
    interval_ms: PositiveInt
    max_retries: PositiveInt
    exponent: NonNegativeInt
    jitter_ms: PositiveInt
    interval_cap_ms: PositiveInt
