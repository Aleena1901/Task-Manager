from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
from ..models import User, UserCreate, UserResponse, TokenResponse
from dotenv import load_dotenv
import os
import traceback

load_dotenv()

router = APIRouter(tags=["Authentication"])

# Security configurations
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# JWT configurations
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set in environment variables")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Utility Functions ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hashed version"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a hashed version of the password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- Authentication Dependencies ---

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Dependency to get the current user from the JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception

    user = await User.find_one(User.email == email)
    if user is None:
        raise credentials_exception
    return user

# --- Authentication Routes ---

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    """Register a new user"""
    try:
        print(f"Attempting to create user with email: {user_data.email} and username: {user_data.username}")
        
        # Check for existing user with same email or username
        existing_user = await User.find_one(
            {"$or": [
                {"email": user_data.email},
                {"username": user_data.username}
            ]}
        )
        
        if existing_user:
            detail = "Email already registered" if existing_user.email == user_data.email else "Username already taken"
            print(f"User creation failed: {detail}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail
            )

        # Create new user
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        print("Creating new user in database...")
        await new_user.create()
        print("User created successfully")

        # Generate access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": new_user.email},
            expires_delta=access_token_expires
        )
        print("Access token generated successfully")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse(
                id=str(new_user.id),
                email=new_user.email,
                username=new_user.username,
                is_active=new_user.is_active,
                created_at=new_user.created_at
            ).dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error during signup: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return access token"""
    try:
        print(f"Login attempt for: {form_data.username}")
        user = await User.find_one(
            {"$or": [
                {"email": form_data.username},
                {"username": form_data.username}
            ]}
        )
        print(f"User found: {user is not None}")
        if user:
            print(f"Stored hash: {user.hashed_password}")
            print(f"Password provided: {form_data.password}")
            password_matches = verify_password(form_data.password, user.hashed_password)
            print(f"Password matches: {password_matches}")
        else:
            print("No user found with that email/username.")

        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse(
                id=str(user.id),
                email=user.email,
                username=user.username,
                is_active=user.is_active,
                created_at=user.created_at
            ).dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )

__all__ = ["router", "get_current_user"]