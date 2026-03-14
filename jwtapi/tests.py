import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from sqlalchemy import StaticPool, insert, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException

from main import app, get_db
from database import Base, SECRET_KEY, ALGORITHM
from auth import get_password_hash, verify_password
from auth import create_access_token, get_current_user
from models import User, likes_table



SQLACHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory"
engine = create_async_engine(
    SQLACHEMY_DATABASE_URL,
    connect_args = {"check_same_thread": False},
    poolclass=StaticPool, 
)


TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

async def override_get_db() -> AsyncGenerator:
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def client(db_session):
    yield TestClient(app)


@pytest.fixture(scope="function")
def registered_user(client: TestClient):
    user_data = {"email": "tetsuser@example.com", "password": "testpassword"}
    response = client.post("/register", json=user_data)
    assert response.status_code == 200
    return {"username": user_data["email"], "password": user_data["password"]}


@pytest.fixture(scope="function")
def auth_headers(client: TestClient, registered_user):
    response = client.post("/token", data=registered_user)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}



# unit tests

def test_password_hashing():
    password = "secretpassword"
    hashed_password = get_password_hash(password)
    assert hashed_password != password 
    assert verify_password(password, hashed_password)
    assert not verify_password("wrongpassword", hashed_password)


def test_create_access_token():
    data = {"sub": "test@example.com"}
    token = create_access_token(data)
    assert isinstance(token, str)

# component testing

@pytest.mark.asyncio
async def test_get_current_user(db_session: AsyncSession):
    user_email = "component@test.com"
    hashed_password = get_password_hash("password")
    user = User(email=user_email, hashed_password=hashed_password)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    access_token = create_access_token(data={"sub": user_email})
    current_user = await get_current_user(token=access_token, db=db_session)
    assert current_user is not None
    assert current_user.email == user_email

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(token="invalidtoken", db=db_session)
    assert excinfo.value.status_code == 401

    non_existent_user_token = create_access_token(data={"sub": "nouser@example.com"})
    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(token=non_existent_user_token, db=db_session)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "User not found"

    expire = datetime.now(timezone.utc) - timedelta(minutes=1)
    to_encode = {"sub": user_email, "exp": expire}
    expired_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(token=expired_token, db=db_session)
    assert excinfo.value.status_code == 401



# Integration & API testing 

def test_login(client: TestClient, registered_user):
    response = client.post("/token", data=registered_user)
    assert response.status_code == 200

    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    response = client.post("/token", data={"username": registered_user["username"], "password": "wrongpassword"})
    assert response.status_code == 401



def test_read_users_me(client: TestClient, auth_headers, registered_user):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == registered_user["username"]

def test_create_and_get_post(client: TestClient, auth_headers):
    post_data = {"title": "Test Post", "content": "This is a test post."}
    response = client.post("/posts/", json=post_data, headers=auth_headers)
    assert response.status_code == 201
    created_post = response.json()
    assert created_post["title"] == post_data["title"]
    assert created_post["content"] == post_data["content"]
    assert created_post["likes_count"] == 0
    post_id = created_post["id"]

    response = client.get(f"/posts/{post_id}")
    assert response.status_code == 200
    retrieved_post = response.json()
    assert retrieved_post == created_post

    response = client.get("/posts/")
    assert response.status_code == 200
    posts_list = response.json()
    assert len(posts_list) == 1
    assert posts_list[0] == created_post




def test_delete_post(client: TestClient, auth_headers):
    post_data = {"title": "To Be Deleted", "content": "delete this post."}
    response = client.post("/posts/", json=post_data, headers=auth_headers)
    post_id = response.json()["id"]

    response = client.delete(f"/posts/{post_id}", headers=auth_headers)
    assert response.status_code == 204

    response = client.get(f"/posts/{post_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_likes_count(client: TestClient, auth_headers, db_session: AsyncSession):
    post_data = {"title": "Liked Post", "content": "Content"}
    response = client.post("/posts/", json=post_data, headers=auth_headers)
    assert response.status_code == 201
    post_id = response.json()["id"]

    result = await db_session.execute(select(User).where(User.email == "tetsuser@example.com")) 
    user = result.scalar_one()

    stmt = insert(likes_table).values(user_id=user.id, post_id=post_id)
    await db_session.execute(stmt)
    await db_session.commit()

    response = client.get(f"/posts/{post_id}")
    assert response.status_code == 200
    assert response.json()["likes_count"] == 1