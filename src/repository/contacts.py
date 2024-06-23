from typing import List
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.schemas.schema import ContactSchema, ContactUpdate
from sqlalchemy import select, func

async def get_contacts(limit: int, offset: int, db: AsyncSession, user: User) -> List[Contact]:
    """
    The get_contacts function returns a list of contacts for the given user.
    
    :param limit: int: Limit the number of contacts returned
    :param offset: int: Specify the offset of the first row to return
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Filter the contacts by user
    :return: A list of contact objects
    :doc-author: Trelent
    """
    result = await db.execute(select(Contact).filter(Contact.user_id == user.id).offset(offset).limit(limit))
    return result.scalars().all()



async def get_contact(contact_id: int, db: AsyncSession, user: User) -> Contact:
    """
    The get_contact function returns a contact from the database.
    
    :param contact_id: int: Specify the id of the contact you want to get
    :param db: AsyncSession: Pass the database connection to the function
    :param user: User: Ensure that the user is only able to get contacts that they own
    :return: A contact object
    :doc-author: Trelent
    """
    result = await db.execute(select(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id))
    return result.scalar_one_or_none()
  

async def create_contact(body: ContactSchema, db: AsyncSession, user: User) -> Contact:
    """
    The create_contact function creates a new contact in the database.
    
    :param body: ContactSchema: Validate the request body against the contactschema schema
    :param db: AsyncSession: Interact with the database
    :param user: User: Get the user id from the token
    :return: A contact object
    :doc-author: Trelent
    """
    contact = Contact(**body.model_dump(exclude_unset=True), user=user)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def remove_contact(contact_id: int, db: AsyncSession, user: User) -> Contact | None:
    """
    The remove_contact function removes a contact from the database.
    
    :param contact_id: int: Identify the contact to be deleted
    :param db: AsyncSession: Pass the database session into the function
    :param user: User: Check if the user is authorized to delete the contact
    :return: A contact object or none if the contact does not exist
    :doc-author: Trelent
    """
    result = await db.execute(select(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id))
    contact = result.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact


async def update_contact(contact_id: int, body: ContactUpdate, db: AsyncSession, user: User) -> Contact | None:
    """
    The update_contact function updates a contact in the database.
    
    :param contact_id: int: Identify the contact to update
    :param body: ContactUpdate: Get the data from the request body
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Ensure that the user is only updating their own contacts
    :return: The updated contact or none if the contact doesn't exist
    :doc-author: Trelent
    """
    result = await db.execute(select(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id))
    contact = result.scalar_one_or_none()
    if contact:
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(contact, key, value)
            
        await db.commit()
        await db.refresh(contact)
    return contact


async def search_contacts(query: str, db: AsyncSession, user: User) -> List[Contact]:
    """
    The search_contacts function searches the database for contacts that match a given query.
        The search is case insensitive and will return any contact whose first name, last name, or email address contains the query string.
        The function returns a list of Contact objects.
    
    :param query: str: Search for a contact by name or email
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Ensure that the user is only able to search for contacts they have created
    :return: A list of contacts
    :doc-author: Trelent
    """
    search_query = f"%{query}%"
    result = await db.execute(
        select(Contact).filter(
            (Contact.first_name.ilike(search_query)|
            Contact.last_name.ilike(search_query) |
            Contact.email.ilike(search_query))&
            (Contact.user_id == user.id)
        )
    )
    return result.scalars().all()



async def get_birthdays_within_next_week(db: AsyncSession, user: User) -> List[Contact]:
    """
    The get_birthdays_within_next_week function returns a list of contacts whose birthdays are within the next week.
    
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Get the user_id of the current user
    :return: A list of contacts with birthdays within the next week
    :doc-author: Trelent
    """
    current_date = date.today()
    next_week = current_date + timedelta(days=7)

    current_date_str = current_date.strftime('%m-%d')
    next_week_str = next_week.strftime('%m-%d')

    if current_date.month <= next_week.month:
        result = await db.execute(
            select(Contact).filter(
                func.to_char(Contact.birthday, 'MM-DD').between(current_date_str, next_week_str),
                Contact.user_id == user.id
            )
        )
    else:
        result = await db.execute(
            select(Contact).filter(
                (func.to_char(Contact.birthday, 'MM-DD').between(current_date_str, '12-31')) |
                (func.to_char(Contact.birthday, 'MM-DD').between('01-01', next_week_str)),
                Contact.user_id == user.id
            )
        )

    return result.scalars().all()