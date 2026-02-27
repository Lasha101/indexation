import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from typing import Annotated, List, Optional
from datetime import datetime


from database import Base, engine, get_db
from schemas import UserCreate, UserResponse, Token, PostCreate, PostResponse, PostUpdate
from models import User, Post, likes_table
from auth import verify_password, get_password_hash, create_access_token, get_current_user

@asynccontextmanager
async def lifespan(app: FastAPI):
   
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield 

app = FastAPI(lifespan=lifespan)


@app.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = get_password_hash(user_data.password)
    new_user = User(email=user_data.email, hashed_password=hashed_pwd)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/posts/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession =  Depends(get_db)
):

    new_post = Post(**post_data.model_dump(), user_id=current_user.id)
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)

    new_post.likes_count = 0
    return new_post


@app.get("/posts/", response_model=List[PostResponse])
async def get_posts(
    db: AsyncSession =  Depends(get_db),
    limit: int = Query(10),
    skip: int = Query(0), 
    user_id: Optional[int] = None,
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None,
):
    likes_subquery = select(func.count()).select_from(likes_table).where(\
        likes_table.c.post_id == Post.id).scalar_subquery()

    query = select(Post, likes_subquery.label("likes_count"))

    if user_id:
        query = query.where(Post.user_id == user_id)

    if start_date:
        query = query.where(Post.created_at >= start_date)

    if start_date:
        query = query.where(Post.created_at <= end_date)


    query = query.limit(limit).offset(skip).order_by(Post.created_at.desc())

    result = await db.execute(query)
    posts = []

    for post, count in result.all():
        post.likes_count = count
        posts.append(post)

    return posts

@app.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: AsyncSession =  Depends(get_db)):
    likes_subquery = select(func.count()).select_from(likes_table).where(\
        likes_table.c.post_id == Post.id).scalar_subquery()
    
    query = select(Post, likes_subquery.label("likes_count")).where(Post.id == post_id)
    result = await db.execute(query)
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    post, likes_count = row
    post.likes_count = likes_count 

    return post


@app.get("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user), 
    db: AsyncSession =  Depends(get_db)
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Notauthorized to delete this post"
        )
    
    await db.delete(post)
    await db.commit()

    return None


