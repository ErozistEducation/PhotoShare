from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.database.db import get_db
from src.entity.models import User, Role
from src.schemas.user import UserSchema

async def get_user_by_email(email: str, db: AsyncSession):
    stmt = select(User).filter_by(email=email)
    result = await db.execute(stmt)
    user = result.scalars().first()  # Correctly fetch the first user
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
