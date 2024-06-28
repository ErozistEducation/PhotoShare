from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from src.entity.models import Photo, Tag, User
from src.schemas.photo import PhotoCreate, PhotoUpdate

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
    if photo_data.tags is not None:
        # photo.tags = []
        for tag_name in photo_data.tags:
            tag = await db.execute(select(Tag).filter_by(name=tag_name))
            existing_tag = tag.scalar_one_or_none()
            if existing_tag:
                pass
            else:
                new_tag = Tag(name=tag_name)
                db.add(new_tag)
                await db.flush()
                # photo.tags.append(new_tag)
    db.add(new_photo)
    await db.commit()
    await db.refresh(new_photo)
    return new_photo


async def update_photo(photo_id: int, photo_data: PhotoUpdate, user: User, db: AsyncSession):
    photo = await db.execute(select(Photo).filter_by(id=photo_id, user=user).options(joinedload(Photo.tags)))
    photo = photo.scalar_one_or_none()
    if photo:
        if photo_data.description:
            photo.description = photo_data.description
        
        if photo_data.tags is not None:
            photo.tags = []
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
    photo = await db.execute(select(Photo).filter_by(id=photo_id, user=user))
    photo = photo.scalar_one_or_none()
    if photo:
        await db.delete(photo)
        await db.commit()
    return photo

async def get_photo(photo_id: int, db: AsyncSession):
    photo = await db.execute(select(Photo).filter_by(id=photo_id).options(joinedload(Photo.tags)))
    return photo.scalar_one_or_none()

async def get_photos(user: User, db: AsyncSession):
    photos = await db.execute(select(Photo).filter_by(user=user).options(joinedload(Photo.tags)))
    return photos.scalars().all()
