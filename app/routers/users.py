from fastapi import APIRouter, Depends, HTTPException
from typing import List
from .. import models
from .auth import get_current_user

router = APIRouter()

@router.get("/me", response_model=models.UserResponse)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.get("/", response_model=List[models.UserResponse])
async def read_users(skip: int = 0, limit: int = 100):
    try:
        users = await models.User.find().skip(skip).limit(limit).to_list()
        return users
    except Exception as e:
        print(f"Read users error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching users"
        )

@router.get("/{user_id}", response_model=models.UserResponse)
async def read_user(user_id: str):
    try:
        user = await models.User.get(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        print(f"Read user error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching the user"
        ) 