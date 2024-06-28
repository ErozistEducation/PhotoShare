from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class PhotoBase(BaseModel):
    url: str
    description: Optional[str] = None

class PhotoCreate(PhotoBase):
    tags: Optional[List[str]] = []

class PhotoUpdate(BaseModel):
    description: Optional[str] = None
    tags: Optional[List[str]] = []

class PhotoResponse(PhotoBase):
    id: int
    created_at: datetime
    updated_at: datetime
    tags: List[str]

    model_config = ConfigDict(from_attributes = True)