import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv
from models import User, Task  # Adjust import based on your project structure

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/taskmaster")
DB_NAME = os.getenv("DB_NAME", "taskmaster")

async def init_db():
    client = AsyncIOMotorClient(MONGODB_URL)
    await init_beanie(
        database=client[DB_NAME],
        document_models=[User, Task]
    )
    print("MongoDB initialized with Beanie models.")

if __name__ == "__main__":
    asyncio.run(init_db())
