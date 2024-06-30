import urllib
import cloudinary.uploader
import qrcode
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict
from src.conf.config import config
from src.database.db import get_db
from src.entity.models import User
from src.schemas.photo import PhotoCreate, PhotoUpdate, PhotoResponse
from src.services.auth import auth_service
from src.services.cloudinary import upload_image
from src.repository.photos import create_photo, update_photo, get_photo, get_photos, delete_photo as delete_photo_db, save_transformation_to_db

router = APIRouter(prefix='/photos', tags=['photos'])


class ImageTransformRequest(BaseModel):
    image_url: str
    transformations: Dict[str, str]


@router.post("/", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
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


@router.put("/{photo_id}", response_model=PhotoResponse)
async def update_photo_details(
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
async def delete_photo(
        photo_id: int,
        user: User = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    deleted_photo = await delete_photo_db(photo_id, user, db)
    if not deleted_photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return None


@router.get("/{photo_id}", response_model=PhotoResponse)
async def get_photo_details(
        photo_id: int,
        user: User = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    photo = await get_photo(photo_id, user, db)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return photo


@router.get("/", response_model=List[PhotoResponse])
async def list_photos(
        user: User = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    return await get_photos(user, db)


@router.post("/transform-image/")
async def transform_image(request: ImageTransformRequest):
    cloudinary.config(
        cloud_name=config.CLOUDINARY_NAME,
        api_key=config.CLOUDINARY_API_KEY,
        api_secret=config.CLOUDINARY_API_SECRET
    )

    transformed_url = cloudinary.uploader.upload(request.image_url, **request.transformations)["url"]

    transformation_id = "unique_identifier_for_this_transformation"

    save_transformation_to_db(transformation_id, transformed_url, request.transformations)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(transformed_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    return {
        "transformed_url": transformed_url,
        "qr_code_image": qr_img
    }
