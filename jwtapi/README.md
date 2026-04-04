FastAPI Fundamentals: Minimalist Async API

A streamlined, highly accessible FastAPI web application designed as an educational tool to introduce developers to the core concepts of asynchronous API development.

This project strips away complex boilerplate to clearly demonstrate the fundamental flow of a FastAPI backend: from routing and data validation to the async ORM and JWT authentication. It serves as a perfect starting point for understanding how Python, asynchronous database sessions, and security protocols interact within a modern RESTful architecture.

Features & Concepts Demonstrated

FastAPI Architecture: Clear separation of routing logic, Pydantic validation schemas, and database models.

Database Integration: Utilizing SQLAlchemy's asynchronous Object-Relational Mapper (ORM) connected to a PostgreSQL database.

Authentication & Security: Secure user registration and login flows using bcrypt password hashing and JSON Web Tokens (JWT) via FastAPI's OAuth2PasswordBearer dependency.

CRUD & Relational Data: Processing POST, GET, PUT, and DELETE requests for user posts, demonstrating one-to-many and many-to-many relationships (likes) with dynamic subquery aggregations.

Automated Testing: A comprehensive test suite using pytest and pytest-asyncio, leveraging an isolated in-memory SQLite database to validate unit, component, and API integration behaviors.

Technologies Used

Backend: Python, FastAPI

Database: PostgreSQL (asyncpg driver), SQLite (for testing), SQLAlchemy (AsyncORM)

Security: PyJWT, bcrypt

Testing: Pytest, pytest-asyncio, FastAPI TestClient

Project Structure Highlight

models.py: Defines the User, Post, and likes_table database schemas mapping to the database tables.

schemas.py: Contains Pydantic models (e.g., UserCreate, PostResponse) for strict request validation and automatic response serialization.

auth.py: Handles password hashing, JWT token generation, and the get_current_user dependency used to protect secure routes.

database.py: Configures the asynchronous database engine, connection URLs, and the session generator (get_db).

main.py: The core application file featuring the FastAPI instance, lifespan context manager, and endpoint routing for authentication, users, and posts.