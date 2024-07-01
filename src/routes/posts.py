from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, contains_eager
from pydantic import BaseModel
from typing import List
from src.database.db import get_db
from src.entity.models import Photo, User, Tag
from src.services.auth import auth_service
from src.services.cloudinary import transform_image


router = APIRouter(prefix='/posts', tags=['posts'])

class PostResponse(BaseModel):
    author: str
    tags: List[str]
    ava: List[str]
    post: str

@router.get("/", response_model=List[PostResponse])
async def get_posts(
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Photo)
        .filter_by(user_id=user.id)
        .options(joinedload(Photo.tags), joinedload(Photo.user))
    )
    result = await db.execute(stmt)
    photos = result.scalars().unique().all()

    posts = []
    for photo in photos:
        author = photo.user.username
        tags = [tag.name for tag in photo.tags]
        ava_35 = transform_image(user.avatar, {"width": 35, "height": 35, "crop": "fill"})
        ava_200 = transform_image(user.avatar, {"width": 200, "height": 200, "crop": "fill"})
        post_img = transform_image(photo.url, {"width": 300, "height": 300, "crop": "fill"})
        posts.append(PostResponse(author=author, tags=tags, ava=[ava_35, ava_200], post=post_img))

    return posts