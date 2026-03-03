from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import timedelta
from ..core.database import get_db, User, Document
from ..core.security import (
    hash_password, verify_password, create_access_token,
    generate_api_key, get_current_user
)
from ..core.config import get_settings

settings = get_settings()
router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    department: str = None
    designation: str = None


@router.post("/register")
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")
    user = User(
        email=data.email, name=data.name,
        department=data.department, designation=data.designation,
        hashed_password=hash_password(data.password),
        api_key=generate_api_key(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "email": user.email, "name": user.name,
            "api_key": user.api_key, "is_active": user.is_active}


@router.post("/token")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form.username, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")
    token = create_access_token({"sub": user.id, "email": user.email})
    return {"access_token": token, "token_type": "bearer", "user_id": user.id}


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "name": user.name,
            "department": user.department, "api_key": user.api_key}


@router.post("/regenerate-api-key")
async def regenerate_key(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    new_key = generate_api_key()
    await db.execute(update(User).where(User.id == user.id).values(api_key=new_key))
    await db.commit()
    return {"api_key": new_key}


@router.get("/history")
async def get_history(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    page: int = 1, limit: int = 20,
):
    offset = (page - 1) * limit
    result = await db.execute(
        select(Document).where(Document.user_id == user.id)
        .order_by(Document.created_at.desc()).offset(offset).limit(limit)
    )
    docs = result.scalars().all()
    return {
        "page": page, "limit": limit,
        "documents": [
            {"id": d.id, "filename": d.original_filename, "status": d.status,
             "region": d.region_variant, "pages": d.page_count,
             "created": d.created_at.isoformat() if d.created_at else None,
             "completed": d.completed_at.isoformat() if d.completed_at else None}
            for d in docs
        ]
    }
