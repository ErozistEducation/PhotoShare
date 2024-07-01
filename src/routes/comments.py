from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.database.db import get_db
from src.entity.models import Comment, Photo, User
from src.schemas.comment import CommentCreate, CommentUpdate, CommentResponse
from src.services.auth import auth_service


router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    photo_id: int,
    body: CommentCreate,
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        photo = await db.get(Photo, photo_id)
        if not photo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
        comment = Comment(content=body.content, user_id=user.id, photo_id=photo.id)
        db.add(comment)
        await db.commit()
        await db.refresh(comment)
        return comment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    body: CommentUpdate,
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        comment = await db.get(Comment, comment_id)
        if not comment or comment.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found or forbidden")
        comment.content = body.content
        await db.commit()
        await db.refresh(comment)
        return comment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        comment = await db.get(Comment, comment_id)
        if not comment or comment.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found or forbidden")
        await db.delete(comment)
        await db.commit()
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/photo/{photo_id}", response_model=list[CommentResponse])
async def get_comments_by_photo(
    photo_id: int,
    db: AsyncSession = Depends(get_db)
):
    comments = await db.execute(select(Comment).filter_by(photo_id=photo_id))
    return comments.scalars().all()
