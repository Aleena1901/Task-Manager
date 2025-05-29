from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv
import os
from typing import Optional

# Import models and routers
from app.models import User, Task, HTTPError
from app.routers import auth, tasks, users
from app.database import init_db, close_db, get_database

# Load environment variables
load_dotenv()

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database and Beanie first!
    await init_db()

    # (Optional) Verify required environment variables
    required_vars = ["MONGODB_URL", "DB_NAME", "SECRET_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"⚠️ WARNING: Missing environment variables: {', '.join(missing_vars)}")
        if "SECRET_KEY" in missing_vars:
            print("⚠️ WARNING: Using temporary SECRET_KEY for development")

    # Now it's safe to create indexes
    try:
        await User.get_motor_collection().create_index("email", unique=True)
        await User.get_motor_collection().create_index("username", unique=True)
        await Task.get_motor_collection().create_index("owner_id")
    except Exception as e:
        print(f"Warning: Index creation failed - {str(e)}")

    yield

    # Shutdown
    await close_db()

# Initialize FastAPI app
app = FastAPI(
    title="Task Manager API",
    description="A complete task management system with user authentication",
    version="1.0.0",
    lifespan=lifespan,
    responses={
        400: {"model": HTTPError},
        401: {"model": HTTPError},
        404: {"model": HTTPError},
        422: {"model": HTTPError},
        500: {"model": HTTPError},
    }
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"]
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates configuration
templates = Jinja2Templates(directory="templates")

# Custom exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({"detail": exc.detail}),
        headers=exc.headers if hasattr(exc, "headers") else None
    )

# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    try:
        db = await get_database()
        await db.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )

# Root endpoint
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# API documentation endpoints
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=app.title + " - Swagger UI",
    )

# Include routers with proper prefixes and tags
app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Authentication"]
)

app.include_router(
    users.router,
    prefix="/api/users",
    tags=["Users"],
    dependencies=[Depends(auth.get_current_user)]
)

app.include_router(
    tasks.router,
    prefix="/api/tasks",
    tags=["Tasks"],
    dependencies=[Depends(auth.get_current_user)]
)

# OpenAPI schema customization
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/api/auth/token",
                    "scopes": {}
                }
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi