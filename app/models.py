from beanie import Document, Link
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class User(Document):
    email: EmailStr
    username: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "users"
        
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "is_active": True
            }
        }

class Task(Document):
    title: str
    description: str
    priority: str
    due_date: Optional[datetime]
    completed: bool = False
    created_at: datetime = datetime.utcnow()
    owner_id: str

    class Settings:
        name = "tasks"
        
    class Config:
        schema_extra = {
            "example": {
                "title": "Complete project",
                "description": "Finish the project documentation",
                "priority": "high",
                "due_date": "2024-01-01T00:00:00",
                "completed": False
            }
        }

# Pydantic models for request/response
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    is_active: bool

class TaskCreate(BaseModel):
    title: str
    description: str
    priority: str
    due_date: Optional[datetime]

class TaskUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    priority: Optional[str]
    due_date: Optional[datetime]
    completed: Optional[bool] 