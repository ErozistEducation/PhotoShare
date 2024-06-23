from unittest.mock import Mock,MagicMock,ANY

import pytest
from sqlalchemy import select

from src.entity.models import User
from tests.conftest import TestingSessionLocal
from src.services.auth import auth_service
# from src.conf import messages

user_data = {"username": "ali", "email": "ali@gmail.com", "password": "12345678"}
test_user = {"username": "deadpool", "email": "deadpool@example.com", "password": "12345678"}



def test_signup(client, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response = client.post("/api/auth/signup", json=user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "password" not in data
    assert "avatar" in data



def test_repeat_signup(client):
    response = client.post("/api/auth/signup", json=test_user)
    assert response.status_code == 409
    data = response.json()
    assert data["detail"] == "Account already exists"



def test_not_confirmed_login(client):
    response = client.post("api/auth/login",
                           data={"username": user_data.get("email"), "password": user_data.get("password")})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Email not confirmed"



@pytest.mark.asyncio
async def test_login(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).filter(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()

    response = client.post("/api/auth/login",
                           data={"username": user_data.get("email"), "password": user_data.get("password")})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"



def test_wrong_email_login(client):
    response = client.post("api/auth/login",
                           data={"username": "email", "password": user_data.get("password")})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid email"



def test_wrong_password_login(client):
    response = client.post("api/auth/login",
                           data={"username": user_data.get("email"), "password": "password"})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid password"



def test_invalid_refresh_token(client):
    response = client.get("/api/auth/refresh_token", headers={"Authorization": "Bearer invalid_refresh_token"})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Could not validate credentials"



@pytest.mark.asyncio
async def test_refresh_token(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).filter(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()
        refresh_token = await auth_service.create_refresh_token(data={"sub": user_data["email"]})
        current_user.refresh_token = refresh_token
        await session.commit()
    response = client.get("/api/auth/refresh_token", headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"



@pytest.mark.asyncio
async def test_confirmed_email_invalid_token(client):
    token = "invalid_token"
    response = client.get(f"/api/auth/confirmed_email/{token}")
    assert response.status_code == 500, response.text
    data = response.json()
    assert data["detail"] == "An error occurred during email confirmation"



@pytest.mark.asyncio
async def test_confirmed_email(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).filter(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        current_user.confirmed=False
        session.add(current_user)
        await session.commit()
        token = auth_service.create_email_token({"sub": user_data["email"]})
    response = client.get(f"/api/auth/confirmed_email/{token}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Email confirmed"


@pytest.mark.asyncio
async def test_confirmed_email_already_confirmed(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).filter(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user.confirmed:
            token = auth_service.create_email_token({"sub": user_data["email"]})
    response = client.get(f"/api/auth/confirmed_email/{token}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Your email is already confirmed"



@pytest.mark.asyncio
async def test_confirmed_email_verification_error(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).filter(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user is None:
            response = client.get(f"/api/auth/confirmed_email/{current_user}")
            assert response.status_code == 400, response.text
            data = response.json()
            assert data["detail"] == "Verification error"




@pytest.mark.asyncio
async def test_request_email_user_confirmed(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).filter(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user.confirmed :
            response = client.post("/api/auth/request_email", json={"email": user_data["email"]})
            assert response.status_code == 200, response.text
            data = response.json()
            assert data["message"] == "Your email is already confirmed"




@pytest.mark.asyncio
async def test_request_email_user_not_confirmed(client, monkeypatch):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).filter(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        current_user.confirmed=False
        session.add(current_user)
        await session.commit()
        mock_send_email = MagicMock()
        monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
        response = client.post("/api/auth/request_email", json={"email": user_data["email"]})
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["message"] == "Check your email for confirmation."
        mock_send_email.assert_called_once_with(user_data["email"], user_data["username"], ANY)




@pytest.mark.asyncio
async def test_request_email_user_not_foundr(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).filter(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user is None:
            response = client.post("/api/auth/request_email", json={"email": "none@example.com"})
            assert response.status_code == 404, response.text
            data = response.json()
            assert data["detail"] == "User not found"






