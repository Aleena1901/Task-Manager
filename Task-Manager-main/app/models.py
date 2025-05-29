from beanie import Document
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re

# --- Enums ---
class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# --- Database Models ---
class User(Document):
    email: EmailStr
    username: str = Field(..., min_length=1, max_length=50)
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    class Settings:
        name = "users"
        indexes = [
            "email",  # Default index
            "username"  # Default index
        ]

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "is_active": True,
                "created_at": "2023-01-01T00:00:00"
            }
        }

class Task(Document):
    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(default="", max_length=1000)
    priority: Priority = Priority.MEDIUM
    due_date: Optional[datetime] = None
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    owner_id: str  # Reference to User.id

    class Settings:
        name = "tasks"
        indexes = [
            "owner_id",
            "completed",
            "due_date",
            "priority"
        ]

    class Config:
        schema_extra = {
            "example": {
                "title": "Complete project",
                "description": "Finish the project documentation",
                "priority": "high",
                "due_date": "2024-01-01T00:00:00",
                "completed": False,
                "owner_id": "507f1f77bcf86cd799439011"
            }
        }

# --- Authentication Models ---
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    is_active: bool
    created_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserInDB(UserResponse):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[EmailStr] = None

class TokenResponse(Token):
    user: UserResponse

# --- Task Models ---
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(default="", max_length=1000)
    priority: Priority = Priority.MEDIUM
    due_date: Optional[datetime] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    priority: Optional[Priority] = None
    due_date: Optional[datetime] = None
    completed: Optional[bool] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    priority: Priority
    due_date: Optional[datetime]
    completed: bool
    created_at: datetime
    updated_at: Optional[datetime]
    owner_id: str

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# --- Utility Models ---
class Message(BaseModel):
    detail: str

class HTTPError(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {"detail": "HTTPException raised."}
        }

__all__ = [
    'User', 'Task', 'UserCreate', 'UserResponse', 'UserInDB',
    'Token', 'TokenData', 'TokenResponse', 'TaskCreate',
    'TaskUpdate', 'TaskResponse', 'Priority', 'Message', 'HTTPError'
]