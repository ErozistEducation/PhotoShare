import logging
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from src.entity.models import Photo, Tag, User
from src.schemas.photo import PhotoCreate, PhotoUpdate



logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def create_photo(photo_data: PhotoCreate, user: User, db: AsyncSession):
    new_photo = Photo(
        url=photo_data.url,
        description=photo_data.description,
        user_id=user.id
    )
    if photo_data.tags is not None:
        for tag_name in photo_data.tags:
            tag = await db.execute(select(Tag).filter_by(name=tag_name))
            existing_tag = tag.scalar_one_or_none()
            if existing_tag:
                new_photo.tags.append(existing_tag)
            else:
                new_tag = Tag(name=tag_name)
                db.add(new_tag)
                await db.flush()
                new_photo.tags.append(new_tag)
    
    db.add(new_photo)
    await db.commit()
    await db.refresh(new_photo)
    return new_photo


async def update_photo(photo_id: int, photo_data: PhotoUpdate, user: User, db: AsyncSession):
    stmt = select(Photo).filter_by(id=photo_id, user_id=user.id).options(joinedload(Photo.tags))
    result = await db.execute(stmt)
    photo = result.unique().scalar_one_or_none()
    if photo:
        photo.description = photo_data.description
        await db.commit()
        await db.refresh(photo)
    return photo

async def delete_photo(photo_id: int, user: User, db: AsyncSession):
    stmt = select(Photo).filter_by(id=photo_id, user_id=user.id).options(joinedload(Photo.tags))
    result = await db.execute(stmt)
    photo = result.unique().scalar_one_or_none()
    if photo:
        await db.delete(photo)
        await db.commit()
    return photo

async def get_photo(photo_id: int, db: AsyncSession):
    stmt = select(Photo).filter_by(id=photo_id).options(joinedload(Photo.tags))
    result = await db.execute(stmt)
    photo = result.unique().scalar_one_or_none()
    return photo

async def get_photos(user: User, db: AsyncSession):
    stmt = select(Photo).filter_by(user_id=user.id).options(joinedload(Photo.tags))
    result = await db.execute(stmt)
    photos = result.unique().scalars().all()
    return photos

async def add_tags_to_photo(photo_id: int, tags: List[str], user: User, db: AsyncSession):
    logger.debug("Received request to add tags to photo with ID: %d for user: %d", photo_id, user.id)
    stmt = select(Photo).filter_by(id=photo_id, user_id=user.id).options(joinedload(Photo.tags))
    result = await db.execute(stmt)
    photo = result.unique().scalar_one_or_none()
    if photo:
        if len(photo.tags) + len(tags) > 5:
            raise ValueError("Cannot add more than 5 tags to a photo")
        for tag_name in tags:
            tag = await db.execute(select(Tag).filter_by(name=tag_name))
            existing_tag = tag.scalar_one_or_none()
            if existing_tag:
                if existing_tag not in photo.tags:
                    photo.tags.append(existing_tag)
                    logger.debug("Tag '%s' added to photo ID: %d", tag_name, photo_id)
            else:
                new_tag = Tag(name=tag_name)
                db.add(new_tag)
                await db.flush()
                photo.tags.append(new_tag)
                logger.debug("New tag '%s' created and added to photo ID: %d", tag_name, photo_id)
                
    if photo_data.tags is not None:
        for tag_name in photo_data.tags:
            tag = await db.execute(select(Tag).filter_by(name=tag_name))
            existing_tag = tag.scalar_one_or_none()
            if existing_tag:
                new_photo.tags.append(existing_tag)
            else:
                new_tag = Tag(name=tag_name)
                db.add(new_tag)
                await db.flush()
                new_photo.tags.append(new_tag)
                
        await db.commit()
        await db.refresh(photo)
        logger.debug("Tags added successfully to photo ID: %d for user: %d", photo_id, user.id)
    return photo

#####################
transformations_db = {}


def save_transformation_to_db(transformation_id: str,
                              transformed_url: str,
                              transformations: Dict[str, str]):
    transformations_db[transformation_id] = {'transformed_url': transformed_url,'transformations': transformations}
