from typing import List
from fastapi import APIRouter, HTTPException, Depends, status, Path, Query

from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.schemas.schema import  ContactSchema, ContactUpdate, ContactResponse
from src.repository import contacts as repository_contacts
from src.services.auth import auth_service
from src.entity.models import User
from fastapi_limiter.depends import RateLimiter

router = APIRouter(prefix='/contacts', tags=["contacts"])


@router.get("/", response_model=List[ContactResponse], description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def get_contacts(limit: int = Query(10, ge=10, le=500), offset: int = Query(0, ge=0), db: AsyncSession = Depends(get_db),
                       user: User = Depends(auth_service.get_current_user)):
    """
    The get_contacts function returns a list of contacts for the current user.
        The limit and offset parameters are used to paginate the results.
    
    
    :param limit: int: Limit the number of contacts returned
    :param ge: Specify that the limit must be greater than or equal to 10
    :param le: Limit the number of contacts returned
    :param offset: int: Specify the number of records to skip
    :param ge: Specify the minimum value of the limit parameter
    :param db: AsyncSession: Pass the database session to the repository layer
    :param user: User: Get the current user from the auth_service
    :return: A list of contacts
    :doc-author: Trelent
    """
    contacts = await repository_contacts.get_contacts( limit, offset, db, user)
    return contacts




@router.get("/{contact_id}", response_model=ContactResponse, description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def get_contact(contact_id: int, db: AsyncSession = Depends(get_db), 
                      user: User = Depends(auth_service.get_current_user)):
    """
    The get_contact function returns a contact by its id.
        If the user is not logged in, an HTTP 401 Unauthorized response is returned.
        If the contact does not exist, an HTTP 404 Not Found response is returned.
    
    :param contact_id: int: Get the contact id from the url
    :param db: AsyncSession: Pass the database session to the repository layer
    :param user: User: Check if the user is authorized to view the contact
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await repository_contacts.get_contact(contact_id, db, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact



@router.post("/", response_model=ContactResponse, description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=5, seconds=60))], status_code=status.HTTP_201_CREATED)
async def create_contact(body: ContactSchema, db: AsyncSession = Depends(get_db), 
                         user: User = Depends(auth_service.get_current_user)):
    """
    The create_contact function creates a new contact in the database.
        The function takes a ContactSchema object as input, and returns the newly created contact.
    
    
    :param body: ContactSchema: Validate the request body
    :param db: AsyncSession: Pass the database session into the function
    :param user: User: Get the user_id from the token
    :return: The contact object, which is a dict
    :doc-author: Trelent
    """
    return await repository_contacts.create_contact(body, db, user)



@router.put("/{contact_id}", response_model=ContactResponse, description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def update_contact(body: ContactUpdate, contact_id: int, db: AsyncSession = Depends(get_db), 
                         user: User = Depends(auth_service.get_current_user)):
    """
    The update_contact function updates a contact in the database.
        The function takes a ContactUpdate object, which is defined in models.py, and uses it to update the contact with 
        id = contact_id. If no such contact exists, an HTTP 404 error is raised.
    
    :param body: ContactUpdate: Pass the data that will be used to update the contact
    :param contact_id: int: Get the contact id from the url
    :param db: AsyncSession: Get the database session
    :param user: User: Get the current user from the database
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await repository_contacts.update_contact(contact_id, body, db, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact



@router.delete("/{contact_id}", response_model=ContactResponse)
async def remove_contact(contact_id: int, db: AsyncSession = Depends(get_db), 
                         user: User = Depends(auth_service.get_current_user)):
    """
    The remove_contact function removes a contact from the database.
        Args:
            contact_id (int): The id of the contact to be removed.
            db (AsyncSession, optional): An async session for interacting with the database. Defaults to Depends(get_db).
            user (User, optional): A User object representing the current user making this request. Defaults to Depends(auth_service.get_current_user).
    
    :param contact_id: int: Specify the contact id of the contact to be removed
    :param db: AsyncSession: Pass the database session to the repository layer
    :param user: User: Get the current user from the auth_service
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await repository_contacts.remove_contact(contact_id, db, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact



@router.get("/search/", response_model=List[ContactResponse],description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def search_contacts(query: str, db: AsyncSession = Depends(get_db), 
                          user: User = Depends(auth_service.get_current_user)):
    """
    The search_contacts function searches for contacts in the database.
        Args:
            query (str): The search term to use when searching for contacts.
            db (AsyncSession): An async session object used to interact with the database.
            user (User): A User object representing the current user making this request.
    
    :param query: str: Search for contacts in the database
    :param db: AsyncSession: Pass the database session to the repository layer
    :param user: User: Get the current user
    :return: A list of contacts
    :doc-author: Trelent
    """
    contacts = await repository_contacts.search_contacts(query, db, user)
    return contacts



@router.get("/birthdays/", response_model=List[ContactResponse],description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def get_upcoming_birthdays(db: AsyncSession = Depends(get_db),
                                  user: User = Depends(auth_service.get_current_user)):
    """
    The get_upcoming_birthdays function returns a list of contacts that have birthdays within the next week.
        The user is authenticated using the auth_service dependency, and then passed to the repository function.
    
    :param db: AsyncSession: Get the database session
    :param user: User: Get the current user
    :return: A list of contacts
    :doc-author: Trelent
    """
    contacts = await repository_contacts.get_birthdays_within_next_week(db, user)
    return contacts