import urllib
import logging
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from src.conf.config import config
from src.database.db import get_db
from src.entity.models import User
from src.schemas.photo import PhotoCreate, PhotoUpdate, PhotoResponse2, PhotoBase, PhotoResponse
from src.services.auth import auth_service
from src.services.cloudinary import upload_image
from src.repository.photos import create_photo, update_photo, delete_photo, get_photo, get_photos, add_tags_to_photo

router = APIRouter(prefix='/photos', tags=['photos'])
logging.basicConfig(level=logging.DEBUG)
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
    photo = await add_tags_to_photo(photo_id, tags, user, db)
    if not photo:
        logger.debug("Photo with ID: %d not found for user: %d", photo_id, user.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return photo

#############################

import cloudinary.uploader
import qrcode
from typing import Dict
from pydantic import BaseModel
from src.repository.photos import save_transformation_to_db


class ImageTransformRequest(BaseModel):
    image_url: str
    transformations: Dict[str, str]


@router.get("/transform-image/{image_id}")
def transform_image(image_id: str, width: int = 500, height: int = 500,
                    crop_mode: str = None,
                    rotation: int = 0, filter_type: str = None, overlay_text: str = None):
    cloudinary_params = {
        "api_key": config.CLOUDINARY_API_KEY,
        "width": width,
        "height": height,
        "crop": crop_mode,  # параметр для режиму обрізки
        "angle": rotation,  # кут повороту (градуси)
        "overlay": overlay_text,  # текст на фото
        "effect": filter_type,  # параметр для фільтрів
    }
    cloudinary_url = f"{config.CLOUDINARY_BASE_URL}/image/upload/{image_id}.jpg"
    transformed_url = f"{cloudinary_url}?{urllib.parse.urlencode(cloudinary_params)}"
    return {"transformed_url": transformed_url}



@router.post("/transform-image2/")
async def transform_image2(request: ImageTransformRequest):
    # Конфігурація Cloudinary
    cloudinary.config(
        cloud_name=config.CLOUDINARY_NAME,
        api_key=config.CLOUDINARY_API_KEY,
        api_secret=config.CLOUDINARY_API_SECRET
    )

    # Виконання трансформації зображення за допомогою Cloudinary API
    transformed_url = cloudinary.uploader.upload(request.image_url, **request.transformations)["url"]

    # Генерація унікального ідентифікатора для цього запиту на трансформацію
    transformation_id = "unique_identifier_for_this_transformation"

    # Збереження деталей трансформації в базу даних (псевдокод)
    save_transformation_to_db(transformation_id, transformed_url, request.transformations)

    # Генерація QR-коду для URL трансформованого зображення
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(transformed_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Повернення URL трансформованого зображення та самого QR-коду як відповідь
    return {
        "transformed_url": transformed_url,
        "qr_code_image": qr_img
    }


@router.post("/transform-image3/")
async def transform_image3(request: ImageTransformRequest):
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

