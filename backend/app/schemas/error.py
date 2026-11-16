from typing import List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class FieldValidationError(BaseModel):
    loc: List[Any] = Field(..., description="Location of the invalid field (e.g. ['query', 'limit'])")
    msg: str = Field(..., description="Human-readable explanation of the validation failure")
    type: str = Field(..., description="Validation error code / category")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "loc": ["query", "limit"],
                "msg": "Input should be greater than or equal to 1",
                "type": "greater_than_equal"
            }
        }
    )


class ValidationErrorResponse(BaseModel):
    status_code: int = Field(default=422, description="HTTP status code")
    error: str = Field(default="Unprocessable Entity", description="Standard error title")
    message: str = Field(
        default="Validation failed for one or more request parameters.",
        description="High-level description of what went wrong"
    )
    detail: Any = Field(
        ...,
        description="Detailed breakdown of validation failures or error message string"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status_code": 422,
                "error": "Unprocessable Entity",
                "message": "Validation failed for 'limit': Input should be greater than or equal to 1",
                "detail": [
                    {
                        "loc": ["query", "limit"],
                        "msg": "Input should be greater than or equal to 1",
                        "type": "greater_than_equal"
                    }
                ]
            }
        }
    )


class ErrorResponse(BaseModel):
    status_code: int = Field(..., description="HTTP status code")
    error: str = Field(..., description="HTTP error status message")
    message: str = Field(..., description="Clear explanation of the error")
    detail: str = Field(..., description="Descriptive error detail (compatible with standard clients)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status_code": 403,
                "error": "Forbidden",
                "message": "Privacy policy violation",
                "detail": "Access to 'location' events is restricted by your active privacy settings."
            }
        }
    )
