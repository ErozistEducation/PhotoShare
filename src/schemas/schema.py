from datetime import datetime,date
from typing import List, Optional
from pydantic import BaseModel, Field,EmailStr
from typing import Optional
from src.schemas.user import UserResponse

class ContactSchema(BaseModel):
    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)
    email: EmailStr
    phone: str
    birthday: date
    additional_info: Optional[str] = None

class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    birthday: Optional[date] = None
    additional_info: Optional[str] = None
    
class ContactResponse(ContactSchema):
    id: int
    created_at: datetime | None
    updated_at: datetime | None
    user: UserResponse | None
    # class Config:
    #     orm_mode = True

    class Config:
        from_attributes = True