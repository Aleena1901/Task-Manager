from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from .. import models
from ..routers.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()

class TaskBase(BaseModel):
    title: str
    description: str
    priority: str
    due_date: datetime = None

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: int
    status: str
    created_at: datetime
    owner_id: int

    class Config:
        orm_mode = True

@router.post("/", response_model=models.Task)
async def create_task(task: models.TaskCreate, current_user: models.User = Depends(get_current_user)):
    try:
        db_task = models.Task(
            title=task.title,
            description=task.description,
            priority=task.priority,
            due_date=task.due_date,
            owner_id=str(current_user.id),
            created_at=datetime.utcnow()
        )
        await db_task.insert()
        return db_task
    except Exception as e:
        print(f"Create task error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the task"
        )

@router.get("/", response_model=List[models.Task])
async def read_tasks(skip: int = 0, limit: int = 100, current_user: models.User = Depends(get_current_user)):
    try:
        tasks = await models.Task.find(
            {"owner_id": str(current_user.id)}
        ).skip(skip).limit(limit).to_list()
        return tasks
    except Exception as e:
        print(f"Read tasks error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching tasks"
        )

@router.get("/{task_id}", response_model=models.Task)
async def read_task(task_id: str, current_user: models.User = Depends(get_current_user)):
    try:
        task = await models.Task.find_one({"_id": task_id, "owner_id": str(current_user.id)})
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except Exception as e:
        print(f"Read task error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching the task"
        )

@router.put("/{task_id}", response_model=models.Task)
async def update_task(task_id: str, task_update: models.TaskUpdate, current_user: models.User = Depends(get_current_user)):
    try:
        task = await models.Task.find_one({"_id": task_id, "owner_id": str(current_user.id)})
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        
        update_data = task_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        
        await task.save()
        return task
    except Exception as e:
        print(f"Update task error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while updating the task"
        )

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, current_user: models.User = Depends(get_current_user)):
    try:
        task = await models.Task.find_one({"_id": task_id, "owner_id": str(current_user.id)})
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        
        await task.delete()
        return {"ok": True}
    except Exception as e:
        print(f"Delete task error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while deleting the task"
        ) 