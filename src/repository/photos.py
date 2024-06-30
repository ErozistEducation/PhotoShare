from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from src.entity.models import Photo, Tag, User, Role
from src.schemas.photo import PhotoCreate, PhotoUpdate
from typing import Dict


# async def create_photo(photo_data: PhotoCreate, user: User, db: AsyncSession):
#     new_photo = Photo(
#         url=photo_data.url,
#         description=photo_data.description,
#         user_id=user.id,
#     )
#     new_tags = Tag(name=str(photo_data.tags))
#     db.add(new_photo)
#     db.add(new_tags)
#     await db.commit()
#     await db.refresh(new_photo)

async def create_photo(photo_data: PhotoCreate, user: User, db: AsyncSession):
    new_photo = Photo(
        url=photo_data.url,
        description=photo_data.description,
        user_id=user.id
    )
    if photo_data.tags:
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
    photo_query = select(Photo).filter_by(id=photo_id).options(joinedload(Photo.tags))
    if user.role != Role.admin:
        photo_query = photo_query.filter_by(user_id=user.id)
    photo = await db.execute(photo_query)
    photo = photo.scalar_one_or_none()
    if photo:
        if photo_data.description is not None:
            photo.description = photo_data.description
        if photo_data.tags is not None:
            photo.tags.clear()
            for tag_name in photo_data.tags:
                tag = await db.execute(select(Tag).filter_by(name=tag_name))
                existing_tag = tag.scalar_one_or_none()
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


async def delete_photo(photo_id: int, user: User, db: AsyncSession):
    photo_query = select(Photo).filter_by(id=photo_id)
    if user.role != Role.admin:
        photo_query = photo_query.filter_by(user_id=user.id)
    photo = await db.execute(photo_query)
    photo = photo.scalar_one_or_none()
    if photo:
        await db.delete(photo)
        await db.commit()
    return photo


async def get_photo(photo_id: int, user: User, db: AsyncSession):
    photo_query = select(Photo).options(joinedload(Photo.tags)).filter_by(id=photo_id)
    if user.role != Role.admin:
        photo_query = photo_query.filter_by(user_id=user.id)
    photo = await db.execute(photo_query)
    return photo.scalar_one_or_none


async def get_photos(user: User, db: AsyncSession):
    photos_query = select(Photo).options(joinedload(Photo.tags))
    if user.role != Role.admin:
        photos_query = photos_query.filter_by(user_id=user.id)
    photos = await db.execute(photos_query)
    return photos.unique().scalars().all()


transformations_db = {}


def save_transformation_to_db(transformation_id: str, transformed_url: str, transformations: Dict[str, str]):
    transformations_db[transformation_id] = {
        'transformed_url': transformed_url,
        'transformations': transformations
    }
