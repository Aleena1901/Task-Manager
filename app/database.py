from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv
import os
from typing import Optional, AsyncGenerator
from .models import User, Task
import asyncio

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/taskmaster")
DB_NAME = os.getenv("DB_NAME", "taskmaster")

# MongoDB Client
client: Optional[AsyncIOMotorClient] = None

async def init_db(retries=3, delay=5):
    global client
    for attempt in range(retries):
        try:
            client = AsyncIOMotorClient(
                MONGODB_URL,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            # Test the connection
            await client.server_info()
            
            # Initialize Beanie with the MongoDB client
            await init_beanie(
                database=client[DB_NAME],
                document_models=[User, Task]
            )
            print(f"Successfully connected to MongoDB on attempt {attempt + 1}!")
            return
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                print("Failed to connect to MongoDB after all attempts")
                raise

async def get_database() -> AsyncGenerator:
    if not client:
        await init_db()
    try:
        yield client[DB_NAME]
    finally:
        pass  # Don't close the client here as it's managed globally

async def close_db():
    if client:
        client.close()
        print("MongoDB connection closed") 
