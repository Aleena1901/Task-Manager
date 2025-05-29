from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv
import os
from typing import Optional
from .models import User, Task
import asyncio

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/taskmaster")
DB_NAME = os.getenv("DB_NAME", "taskmaster")

# MongoDB Client
client: Optional[AsyncIOMotorClient] = None


async def init_db(retries: int = 3, delay: int = 5):
    """
    Initialize MongoDB client and Beanie ODM with retry logic.
    """
    global client
    for attempt in range(1, retries + 1):
        try:
            client = AsyncIOMotorClient(
                MONGODB_URL,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )

            # Test MongoDB connection
            await client.server_info()

            # Initialize Beanie with the database and document models
            await init_beanie(
                database=client[DB_NAME],
                document_models=[User, Task]
            )
            print(f"✅ Successfully connected to MongoDB on attempt {attempt}")
            return

        except Exception as e:
            print(f"❌ Attempt {attempt} to connect to MongoDB failed: {e}")
            if attempt < retries:
                print(f"⏳ Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                print("💥 Failed to connect to MongoDB after all attempts")
                raise


async def get_database():
    """
    Return the database instance. Ensures DB is initialized.
    """
    if not client:
        await init_db()
    return client[DB_NAME]


async def close_db():
    """
    Close the MongoDB connection (if needed, typically on shutdown).
    """
    if client:
        client.close()
        print("🔌 MongoDB connection closed")
