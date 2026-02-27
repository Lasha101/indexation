from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    class Config:
        from_attributes = True

class PostBase(BaseModel):
    title: str
    content: str

class PostCreate(PostBase):
    pass 

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class PostResponse(PostBase):
    id: int
    created_at: datetime
    user_id: int
    likes_count: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str