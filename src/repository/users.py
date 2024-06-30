from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar
from sqlalchemy.orm import joinedload
from src.database.db import get_db
from src.entity.models import User, Role
from src.schemas.user import UserSchema, UserProfileResponse,UserUpdateSchema



async def get_user_by_email(email: str, db: AsyncSession):
    stmt = select(User).filter_by(email=email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    return user

async def create_user(body: UserSchema, role: Role, db: AsyncSession = Depends(get_db)) -> User:
   
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)

    new_user = User(
        username=body.username,
        email=body.email,
        password=body.password,
        role=role,
        avatar=avatar
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def update_token(user: User, token: str | None, db: AsyncSession):
    user.refresh_token = token
    await db.commit()

async def confirmed_email(email: str, db: AsyncSession) -> None:
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()

async def update_avatar_url(email: str, url: str | None, db: AsyncSession) -> User:
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_username(username: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar()


async def get_user_profile(username: str, db: AsyncSession) -> UserProfileResponse:
    result = await db.execute(select(User).filter(User.username == username).options(joinedload(User.photos)))
    user = result.scalar_one_or_none()
    if user is None:
        return None
    photo_count = len(user.photos) if user.photos else 0
    user_profile = UserProfileResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        avatar=user.avatar,
        created_at=user.created_at,
        updated_at=user.updated_at,
        confirmed=user.confirmed,
        role=user.role,
        photo_count=photo_count 
    )
    return user_profile


async def update_own_profile(body: UserUpdateSchema,user: User,db: AsyncSession ):
    from src.services.auth import auth_service 
    result = await db.execute(select(User).filter(User.id == user.id).options(joinedload(User.photos)))
    user = result.scalar_one_or_none()
    if user is None:
        return None
    user.username = body.username
    if body.password:
        user.password = auth_service.get_password_hash(body.password)

    await db.commit()
    await db.refresh(user)
    photo_count = len(user.photos) if user.photos else 0
    user_profile = UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            avatar=user.avatar,
            created_at=user.created_at,
            updated_at=user.updated_at,
            confirmed=user.confirmed,
            role=user.role, 
            photo_count=photo_count 
        )
    return user_profile


async def ban_user(user_id: int, db: AsyncSession) -> dict:
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        return None
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    return {"message": "User banned successfully"}