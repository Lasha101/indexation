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
    user_data = {"email": "testuser@example.com", "password": "testpassword"}
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


def test_login(client: TestClient, registered_user):
    """
    API Test: Test token login endpoint.
    """
    response = client.post("/token", data=registered_user)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Test login with wrong password
    response = client.post("/token", data={"username": registered_user["username"], "password": "wrongpassword"})
    assert response.status_code == 401

def test_read_users_me(client: TestClient, auth_headers, registered_user):
    """
    API Test: Test the /users/me endpoint.
    """
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == registered_user["username"]

def test_create_and_get_post(client: TestClient, auth_headers):
    """
    Integration Test: Test creating a post and then retrieving it.
    """
    # Create post
    post_data = {"title": "Test Post", "content": "This is a test post."}
    response = client.post("/posts/", json=post_data, headers=auth_headers)
    assert response.status_code == 201
    created_post = response.json()
    assert created_post["title"] == post_data["title"]
    assert created_post["content"] == post_data["content"]
    assert created_post["likes_count"] == 0
    post_id = created_post["id"]

    # Get the post back
    response = client.get(f"/posts/{post_id}")
    assert response.status_code == 200
    retrieved_post = response.json()
    assert retrieved_post == created_post

    # Get all posts
    response = client.get("/posts/")
    assert response.status_code == 200
    posts_list = response.json()
    assert len(posts_list) == 1
    assert posts_list[0] == created_post

def test_update_post(client: TestClient, auth_headers):
    """
    API Test: Test updating a post.
    """
    # Create post
    post_data = {"title": "Original Title", "content": "Original Content"}
    response = client.post("/posts/", json=post_data, headers=auth_headers)
    post_id = response.json()["id"]

    # Update post
    update_data = {"title": "Updated Title"}
    response = client.put(f"/posts/{post_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    updated_post = response.json()
    assert updated_post["title"] == "Updated Title"
    assert updated_post["content"] == "Original Content" # content should not change

    update_data = {"content": "Updated Content"}
    response = client.put(f"/posts/{post_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    updated_post = response.json()
    assert updated_post["title"] == "Updated Title"
    assert updated_post["content"] == "Updated Content"

def test_delete_post(client: TestClient, auth_headers):
    """
    API Test: Test deleting a post.
    """
    # Create post
    post_data = {"title": "To Be Deleted", "content": "Delete me."}
    response = client.post("/posts/", json=post_data, headers=auth_headers)
    post_id = response.json()["id"]

    # Delete post
    response = client.delete(f"/posts/{post_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify it's gone
    response = client.get(f"/posts/{post_id}")
    assert response.status_code == 404

def test_unauthorized_post_modification(client: TestClient, registered_user):
    """
    API Test: Ensure a user cannot modify another user's post.
    """
    # User 1 registers and logs in
    user1_creds = registered_user
    user1_login_data = {"username": user1_creds["username"], "password": user1_creds["password"]}
    response = client.post("/token", data=user1_login_data)
    user1_token = response.json()["access_token"]
    user1_headers = {"Authorization": f"Bearer {user1_token}"}

    # User 1 creates a post
    post_data = {"title": "User 1 Post", "content": "Content"}
    response = client.post("/posts/", json=post_data, headers=user1_headers)
    post_id = response.json()["id"]

    # User 2 registers and logs in
    user2_creds = {"username": "user2@example.com", "password": "password2"}
    client.post("/register", json={"email": user2_creds["username"], "password": user2_creds["password"]})
    user2_login_data = {"username": user2_creds["username"], "password": user2_creds["password"]}
    response = client.post("/token", data=user2_login_data)
    user2_token = response.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}

    # User 2 tries to update User 1's post
    update_data = {"title": "Hacked!"}
    response = client.put(f"/posts/{post_id}", json=update_data, headers=user2_headers)
    assert response.status_code == 403

    # User 2 tries to delete User 1's post
    response = client.delete(f"/posts/{post_id}", headers=user2_headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_post_likes_count(client: TestClient, auth_headers, db_session: AsyncSession):
    """
    Integration Test: Verify likes count logic.
    Since there is no public endpoint to like a post, we manually insert a like into the database
    to verify that the get_posts and get_post endpoints correctly aggregate the likes count.
    """
    # 1. Create a post via API
    post_data = {"title": "Liked Post", "content": "Content"}
    response = client.post("/posts/", json=post_data, headers=auth_headers)
    assert response.status_code == 201
    post_id = response.json()["id"]

    # 2. Get the user ID (from the user created by auth_headers fixture)
    result = await db_session.execute(select(User).where(User.email == "testuser@example.com"))
    user = result.scalar_one()

    # 3. Manually insert a like
    stmt = insert(likes_table).values(user_id=user.id, post_id=post_id)
    await db_session.execute(stmt)
    await db_session.commit()

    # 4. Verify count is 1 via API
    response = client.get(f"/posts/{post_id}")
    assert response.status_code == 200
    assert response.json()["likes_count"] == 1