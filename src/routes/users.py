import pickle

import cloudinary
import cloudinary.uploader
from fastapi import APIRouter,HTTPException,Depends,status,Path,Query,UploadFile,File

from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User
from src.schemas.user import UserResponse
from src.services.auth import auth_service
from src.conf.config import config
from src.repository import users as repositories_users


router = APIRouter(prefix="/users", tags=["users"])
cloudinary.config(cloud_name=config.CLOUDINARY_NAME,api_key=config.CLOUDINARY_API_KEY,api_secret=config.CLOUDINARY_API_SECRET, secure=True)


@router.get("/me/",response_model=UserResponse)
async def get_current_user(user: User = Depends(auth_service.get_current_user)):
    """
    The get_current_user function is a dependency that will be injected into the
        get_current_user endpoint. It uses the auth_service to retrieve the current user,
        and returns it if found.
    
    :param user: User: Get the user object from the auth_service
    :return: The current user
    :doc-author: Trelent
    """
    return user



@router.patch("/avatar", response_model=UserResponse)
async def update_avatar(file: UploadFile = File(), user: User = Depends(auth_service.get_current_user), db: AsyncSession = Depends(get_db)):
    """
    The update_avatar function is used to update the avatar of a user.
        The function takes in an UploadFile object, which contains the file that will be uploaded to Cloudinary.
        It also takes in a User object, which is obtained from auth_service's get_current_user function. This ensures that only authenticated users can access this endpoint and change their own avatar image.
        Finally, it takes in an AsyncSession object for database access.
    
    :param file: UploadFile: Get the file from the request
    :param user: User: Get the current user
    :param db: AsyncSession: Get the database session
    :return: A user object
    :doc-author: Trelent
    """
    try:
        public_id = f"hm13{user.email}"
        res = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
        res_url = cloudinary.CloudinaryImage(public_id).build_url(width=250, height=250, crop="fill", version=res.get("version"))
        user = await repositories_users.update_avatar_url(user.email, res_url, db)
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
