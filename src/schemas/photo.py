from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

class PhotoBase(BaseModel):
    url: str
    description: Optional[str] = None

class PhotoCreate(PhotoBase):
    tags: Optional[List[str]] = []

class PhotoUpdate(BaseModel):
    description: Optional[str] = None
    # tags: Optional[List[str]] = []

class TagBase(BaseModel):
    id: int
    name: str
    
    model_config = ConfigDict(from_attributes=True)

class PhotoResponse(BaseModel):
    id: int
    url: str
    description: Optional[str] = None
    tags: List[TagBase] = Field(default_factory=list)
    user_id: int

    model_config = ConfigDict(from_attributes=True)

class PhotoResponse2(PhotoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

