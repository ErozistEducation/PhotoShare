import pickle
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User,Role
from src.schemas.user import UserResponse, UserProfileResponse,UserUpdateSchema
from src.services.auth import auth_service
from src.services.cloudinary import upload_image
from src.repository import users as repositories_users
from src.services.roles import RoleAccess

router = APIRouter(prefix="/users", tags=["users"])

access_to_route_all = RoleAccess([Role.admin, Role.moderator])
access_to_route_admin = RoleAccess([Role.admin])

@router.get(
    "/me",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=1, seconds=60))],
)
async def get_current_user(user: User = Depends(auth_service.get_current_user)):
    return user

@router.patch(
    "/avatar",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=1, seconds=60))],
)
async def update_avatar(file: UploadFile = File(), user: User = Depends(auth_service.get_current_user),
                        db: AsyncSession = Depends(get_db)):
    res_url = upload_image(file.file)
    user = await repositories_users.update_avatar_url(user.email, res_url, db)
    auth_service.cache.set(user.email, pickle.dumps(user))
    auth_service.cache.expire(user.email, 300)
    return user


@router.get("/profile/{username}", response_model=UserProfileResponse)
async def get_user_profile(username: str, db: AsyncSession = Depends(get_db),current_user: User = Depends(auth_service.get_current_user)):
    user_profile =  await repositories_users.get_user_profile(username, db)
    if user_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_profile


@router.put("/profile/me", response_model=UserProfileResponse)
async def update_own_profile(body: UserUpdateSchema,user: User = Depends(auth_service.get_current_user),db: AsyncSession = Depends(get_db)):
    user_profile =  await repositories_users.update_own_profile(body,user, db,)
    if user_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_profile

    
    
    
@router.put("/admin/ban/{user_id}",dependencies=[Depends(access_to_route_all)],response_model=dict)
async def ban_user(user_id: int, user: User = Depends(auth_service.get_current_user), db: AsyncSession = Depends(get_db)):
    user_in_db =  await repositories_users.ban_user( user_id , db)
    # role_access:bool = Depends(RoleAccess([Role.admin]))
    if user_in_db is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_in_db

       
  