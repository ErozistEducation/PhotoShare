import io
import logging
import qrcode
from typing import Dict, List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from src.entity.models import Photo, Tag, User, Role
from src.schemas.photo import PhotoCreate, PhotoUpdate

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def is_admin(user: User) -> bool:
    return user.role == 'admin'


async def create_photo(photo_data: PhotoCreate, user: User, db: AsyncSession):
    new_photo = Photo(
        url=photo_data.url,
        description=photo_data.description,
        user_id=user.id
    )
    if photo_data.tags:
        tags = await get_or_create_tags(photo_data.tags, db)
        new_photo.tags.extend(tags)

    db.add(new_photo)
    await db.commit()
    await db.refresh(new_photo)
    logger.debug("Photo created successfully with ID: %d for user: %d", new_photo.id, user.id)
    return new_photo


async def update_photo(photo_id: int, photo_data: PhotoUpdate, user: User, db: AsyncSession):
    stmt = select(Photo).filter_by(id=photo_id).options(joinedload(Photo.tags))
    if user.role != Role.admin:
        stmt = stmt.filter_by(user_id=user.id)
    result = await db.execute(stmt)
    photo = result.unique().scalar_one_or_none()

    if photo:
        if photo_data.description is not None:
            photo.description = photo_data.description

        if photo_data.tags is not None:
            photo.tags = []
            for tag_name in photo_data.tags:
                tag_result = await db.execute(select(Tag).filter_by(name=tag_name))
                existing_tag = tag_result.scalar_one_or_none()
                if existing_tag:
                    photo.tags.append(existing_tag)
                else:
                    new_tag = Tag(name=tag_name)
                    db.add(new_tag)
                    await db.flush()
                    photo.tags.append(new_tag)

        await db.commit()
        await db.refresh(photo)
        return photo
    else:
        return None


async def delete_photo_handler(photo_id: int, user: User, db: AsyncSession):
    stmt = select(Photo).filter_by(id=photo_id)
    if user.role != Role.admin:
        stmt = stmt.filter_by(user_id=user.id)
    result = await db.execute(stmt)
    photo = result.unique().scalar_one_or_none()

    if not photo:
        return None

    await db.delete(photo)
    await db.commit()
    return photo


async def get_photo(photo_id: int, user: User, db: AsyncSession):
    stmt = select(Photo).filter_by(id=photo_id)

    if user.role != Role.admin:
        stmt = stmt.filter_by(id=photo_id, user_id=user.id)
    else:
        stmt = stmt.filter_by(id=photo_id)

    result = await db.execute(stmt)
    photo = result.unique().scalar_one_or_none()

    if not photo:
        return None

    return photo


async def get_photos(user: User, db: AsyncSession):
    photos_query = select(Photo).options(joinedload(Photo.tags))

    if user.role != Role.admin:
        photos_query= photos_query.filter_by(user_id=user.id)

    photos = await db.execute(photos_query)
    return photos.unique().scalars().all()


async def add_tags_to_photo(photo_id: int, tags: List[str], user: User, db: AsyncSession):
    logger.debug("Received request to add tags to photo with ID: %d for user: %d", photo_id, user.id)

    if is_admin(user):
        stmt = select(Photo).filter_by(id=photo_id).options(joinedload(Photo.tags))
    else:
        stmt = select(Photo).filter_by(id=photo_id, user_id=user.id).options(joinedload(Photo.tags))

    result = await db.execute(stmt)
    photo = result.unique().scalar_one_or_none()

    if not photo:
        logger.error("Photo with ID: %d not found for user: %d", photo_id, user.id)
        return None

    try:
        unique_new_tags = await validate_tags(photo, tags)
    except ValueError as e:
        logger.error(f"Validation error for photo ID {photo_id}: {e}")
        raise e

    tags = await get_or_create_tags(unique_new_tags, db)
    photo.tags.extend(tags)
    await db.commit()
    await db.refresh(photo)
    logger.debug("Tags added successfully to photo ID: %d for user: %d", photo_id, user.id)
    return photo


async def get_or_create_tags(tag_names: List[str], db: AsyncSession):
    tags = []
    for tag_name in tag_names:
        logger.debug("Processing tag: %s", tag_name)
        tag = await db.execute(select(Tag).filter_by(name=tag_name))
        existing_tag = tag.scalar_one_or_none()
        if existing_tag:
            logger.debug("Existing tag found: %s", tag_name)
            tags.append(existing_tag)
        else:
            logger.debug("Creating new tag: %s", tag_name)
            new_tag = Tag(name=tag_name)
            db.add(new_tag)
            await db.flush()
            tags.append(new_tag)
            logger.debug("New tag created: %s", tag_name)
    return tags


async def validate_tags(photo: Photo, new_tags: List[str], user: User):
    existing_tags = {tag.name for tag in photo.tags}
    unique_new_tags = [tag for tag in new_tags if tag not in existing_tags]

    if not is_admin(user) and len(photo.tags) + len(unique_new_tags) > 5:
        logger.error("Cannot add more than 5 tags to photo with ID: %d", photo.id)
        raise ValueError("Cannot add more than 5 tags to a photo")

    if not unique_new_tags:
        logger.debug("All tags already exist for photo ID: %d", photo.id)
        raise ValueError("All tags already exist for this photo")

    logger.debug("Tags validated successfully for photo ID: %d by user ID: %d", photo.id, user.id)
    return unique_new_tags


async def remove_tags_from_photo(photo_id: int, tags: List[str], user: User, db: AsyncSession):
    logger.debug("Received request to remove tags from photo with ID: %d for user: %d", photo_id, user.id)

    if is_admin(user):
        stmt = select(Photo).filter_by(id=photo_id).options(joinedload(Photo.tags))
    else:
        stmt = select(Photo).filter_by(id=photo_id, user_id=user.id).options(joinedload(Photo.tags))

    result = await db.execute(stmt)
    photo = result.unique().scalar_one_or_none()

    if not photo:
        logger.error("Photo with ID: %d not found for user: %d", photo_id, user.id)
        return None

    tags_to_remove = [tag for tag in photo.tags if tag.name in tags]
    if not tags_to_remove:
        logger.error("No matching tags found for photo ID: %d", photo_id)
        raise ValueError("No matching tags found for this photo")

    for tag in tags_to_remove:
        photo.tags.remove(tag)

    await db.commit()
    await db.refresh(photo)
    logger.debug("Tags removed successfully from photo ID: %d for user: %d", photo_id, user.id)
    return photo


def generate_qr_code(data: str):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer)
    buffer.seek(0)
    return buffer
