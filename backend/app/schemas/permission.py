from datetime import datetime
from typing import Dict
from pydantic import BaseModel, Field, ConfigDict
from app.models.event import EventCategory


class PermissionUpdate(BaseModel):
    category: EventCategory = Field(..., description="Event category to update")
    is_enabled: bool = Field(..., description="True to enable access, False to restrict")


class PermissionResponse(BaseModel):
    category: str
    is_enabled: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PermissionsState(BaseModel):
    permissions: Dict[str, bool] = Field(
        ...,
        description="Map of category names to their boolean enabled state"
    )
