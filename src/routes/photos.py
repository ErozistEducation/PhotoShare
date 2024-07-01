import logging
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from src.database.db import get_db
from src.entity.models import User
from src.schemas.photo import PhotoCreate, PhotoUpdate, PhotoResponse2, PhotoBase, PhotoResponse, TransformationParams
from src.services.auth import auth_service
from src.services.cloudinary import upload_image, transform_image
from src.repository.photos import create_photo, update_photo, delete_photo, get_photo, get_photos, add_tags_to_photo, remove_tags_from_photo, generate_qr_code


router = APIRouter(prefix='/photos', tags=['photos'])

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


@router.post("/", response_model=PhotoBase, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    description: Optional[str] = None,
    file: UploadFile = File(...),
    tags: List[str] = [],
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    url = upload_image(file.file)
    photo_data = PhotoCreate(url=url, description=description, tags=tags)
    return await create_photo(photo_data, user, db)


@router.put("/{photo_id}", response_model=PhotoResponse2)
async def update_photo_description(
    photo_id: int,
    photo_data: PhotoUpdate,
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    updated_photo = await update_photo(photo_id, photo_data, user, db)
    if not updated_photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return updated_photo


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delet_photo(
    photo_id: int,
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    deleted_photo = await delete_photo(photo_id, user, db)
    if not deleted_photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return None


@router.get("/{photo_id}", response_model=PhotoResponse2)
async def get_photo_details(
    photo_id: int,
    db: AsyncSession = Depends(get_db)
):
    photo = await get_photo(photo_id, db)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return photo


@router.get("/", response_model=list[PhotoResponse2])
async def list_all_photos(
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    photos = await get_photos(user, db)
    return photos


@router.post("/{photo_id}/tags", response_model=PhotoResponse, status_code=status.HTTP_200_OK)
async def add_tags(photo_id: int,
                   tags: List[str],
                   user: User = Depends(auth_service.get_current_user),
                   db: AsyncSession = Depends(get_db)):
    logger.debug("Received request to add tags to photo with ID: %d", photo_id)
    try:
        photo = await add_tags_to_photo(photo_id, tags, user, db)
    except ValueError as e:
        logger.error(f"Error adding tags to photo ID {photo_id}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not photo:
        logger.debug("Photo with ID: %d not found for user: %d", photo_id, user.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return photo


@router.delete("/{photo_id}/tags", response_model=PhotoResponse, status_code=status.HTTP_200_OK)
async def remove_tags(photo_id: int,
                      tags: List[str],
                      user: User = Depends(auth_service.get_current_user),
                      db: AsyncSession = Depends(get_db)):
    logger.debug("Received request to remove tags from photo with ID: %d", photo_id)
    try:
        photo = await remove_tags_from_photo(photo_id, tags, user, db)
    except ValueError as e:
        logger.error(f"Error removing tags from photo ID {photo_id}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not photo:
        logger.debug("Photo with ID: %d not found for user: %d", photo_id, user.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return photo


@router.post("/{photo_id}/transform", response_model=str, status_code=status.HTTP_200_OK)
async def transform_photo(
    photo_id: int,
    transformation_params: TransformationParams,
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    photo = await get_photo(photo_id, db)
    if not photo or photo.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found or access denied")

    transformed_url = transform_image(photo.url, transformation_params.model_dump(exclude_unset=True))
    if transformed_url == photo.url:
        logger.error(f"Transformation did not change the URL: {transformed_url}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Transformation failed")

    return transformed_url


@router.post("/qr-code", response_model=str, status_code=status.HTTP_201_CREATED)
async def create_qr_code(
    photo_id: int,
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    photo = await get_photo(photo_id, db)
    if not photo or photo.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found or access denied")
    
    qr_code_image = generate_qr_code(photo.url)
    return StreamingResponse(qr_code_image, media_type="image/jpg")
