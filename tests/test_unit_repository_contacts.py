from freezegun import freeze_time
import unittest
from unittest.mock import MagicMock, AsyncMock, Mock

from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact,User
from src.schemas.schema import ContactSchema, ContactUpdate
from src.repository.contacts import get_contacts, get_contact, create_contact, remove_contact, update_contact, search_contacts, get_birthdays_within_next_week




class TestAsyncContacts(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.user = User(id=1, username='test_user', password="qwerty", confirmed=True)
        self.session = AsyncMock(spec=AsyncSession)
    

    async def test_get_contacts(self):
        limit = 10
        offset = 0
        contacts = [
            Contact(id=1, first_name="John", last_name="Doe", email="john@example.com", user_id=1),
            Contact(id=2, first_name="Jane", last_name="Smith", email="jane@example.com", user_id=2)
        ]
        mock_contact = MagicMock()
        mock_contact.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mock_contact
        result = await get_contacts(limit, offset, self.session, self.user)
        self.assertEqual(result, contacts)



    async def test_get_contact(self):
        contact = Contact(id=1, first_name="John", last_name="Doe", email="john@example.com", user_id=1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = contact
        self.session.execute.return_value = mock_result
        result = await get_contact(contact_id=1, db=self.session, user=self.user)
        self.assertEqual(result, contact)



    async def test_get_contact_not_found(self):
        contact = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        self.session.execute.return_value = mock_result
        result = await get_contact(contact_id=1, db=self.session, user=self.user)
        self.assertIsNone(result)


    async def test_create_contact(self):
        body = ContactUpdate(first_name="John", last_name="Doe", email="john@example.com",phone = "12340000",
    birthday=date(1990, 10, 10))
        result = await create_contact(body, self.session, self.user)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.birthday, body.birthday)
        

    async def test_update_contact(self):
        body = ContactSchema(first_name="John", last_name="Doe", email="john@example.com",phone = "12345678",
    birthday=date(1990, 10, 10))
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = Contact(id=1,first_name="Jane", last_name="Smith", email="jane@example.com", user_id=2)
        self.session.execute.return_value = mocked_contact
        result = await update_contact(1, body, self.session, self.user)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.birthday, body.birthday)
        
       

    
    async def test_update_contact_not_found(self):
        body = ContactUpdate(first_name="John", last_name="Doe", email="john@example.com",phone = "12340000",
    birthday=date(1990, 10, 10))
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = None
        self.session.execute.return_value = mocked_contact
        result = await update_contact(1, body, self.session, self.user)
        self.assertIsNone(result)
        


    async def test_remove_contact(self):
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = Contact(id=1, first_name="John", last_name="Doe", email="john@example.com", user_id=1)
        self.session.execute.return_value = mocked_contact
        result = await remove_contact(1, self.session, self.user)
        self.session.delete.assert_called_once()
        self.session.commit.assert_called_once()
        self.assertIsInstance(result, Contact)
       


    async def test_remove_contact_not_found(self):
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = None
        self.session.execute.return_value = mocked_contact
        result = await remove_contact(1, self.session, self.user)
        self.session.delete.assert_not_called()  
        self.session.commit.assert_not_called()
        self.assertIsNone(result, Contact)
       


    async def test_search_contacts(self):
        contacts = [
            Contact(id=1, first_name="Jane", last_name="Doe", email="john@example.com", user_id=1),
            Contact(id=2, first_name="Jane", last_name="Smith", email="jane@example.com", user_id=1)
        ]
        mocked_contact = MagicMock()
        mocked_contact.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contact
        result = await search_contacts("Jane", self.session, self.user)
        self.assertEqual(result, contacts)
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[1], Contact)
        self.assertIsInstance(result[0], Contact)
        self.assertEqual(result[1].first_name, "Jane")
        self.assertEqual(result[1].last_name, "Smith")
        self.assertEqual(result[1].email, "jane@example.com")

    

    

    async def test_get_birthdays_within_next_week(self):
        contacts = [
        Contact(id=1, first_name="John", last_name="Doe", birthday=date(2000, 6, 15), user_id=1),
        Contact(id=2, first_name="Jane", last_name="Smith", birthday=date(2000, 6, 25), user_id=1),
        Contact(id=3, first_name="Alice", last_name="Johnson", birthday=date(2000, 10, 20), user_id=1)
        
    ]
        mocked_contact = MagicMock()
        mocked_contact.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contact
        result = await get_birthdays_within_next_week(self.session, self.user)
        self.assertEqual(result, contacts)
        self.assertIsInstance(result[1], Contact)
        self.assertIsInstance(result[0], Contact)
   
   

   
