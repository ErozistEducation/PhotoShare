from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.database.db import get_db
from src.entity.models import User
from src.schemas.user import UserSchema


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    """
    The get_user_by_email function returns a user object from the database based on the email address provided.
        If no user is found, None is returned.
    
    :param email: str: Specify the email of the user we want to get
    :param db: AsyncSession: Pass the database session to the function
    :return: A user object
    :doc-author: Trelent
    """
    user = await db.execute( select(User).filter_by(email=email))
    user = user.scalar_one_or_none()
    return user


async def create_user(body: UserSchema, db: AsyncSession = Depends(get_db)):
    """
    The create_user function creates a new user in the database.
        It takes a UserSchema object as input and returns the newly created user.
    
    :param body: UserSchema: Deserialize the request body into a userschema object
    :param db: AsyncSession: Pass in the database session to be used
    :return: A user object, which is then serialized into a json response
    :doc-author: Trelent
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)
    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: AsyncSession):
    """
    The update_token function updates the user's refresh token in the database.
    
    :param user: User: Get the user object from the database
    :param token: str | None: Set the refresh_token field of the user
    :param db: AsyncSession: Commit the changes to the database
    :return: Nothing, so it should be declared as returning none
    :doc-author: Trelent
    """
    user.refresh_token = token
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession) -> None:
    """
    The confirmed_email function marks a user as confirmed in the database.
    
    :param email: str: Pass the email of the user to be confirmed
    :param db: AsyncSession: Pass the database connection to the function
    :return: None, so the return type is none
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()



async def update_avatar_url(email: str, url: str | None, db: AsyncSession) -> User:
    """
    The update_avatar_url function updates the avatar url of a user.
    
    :param email: str: Get the user by email
    :param url: str | None: Specify the new avatar url
    :param db: AsyncSession: Pass the database session to the function
    :return: The updated user object
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user