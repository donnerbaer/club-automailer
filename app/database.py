"""Database helpers for the application.

This module centralises the SQLAlchemy configuration used by the app. It
defines the default `DATABASE_URL` and exposes common objects that other
modules can import: `engine`, `SessionLocal` and `Base` (the declarative
base class).

Notes:
- The default `DATABASE_URL` points to a local SQLite file for
	development and testing. In production this should be replaced with a
	real database URL (Postgres, MySQL, etc.), typically provided via an
	environment variable.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Default database URL used for development. Replace with a production URL
# via configuration or environment variables when deploying.
DATABASE_URL = "sqlite:///./test.db"

# Create the SQLAlchemy engine. For SQLite we set `check_same_thread=False`
# because the connection may be used across threads by the web server.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Factory for creating new Session objects. Import and call `SessionLocal()`
# where you need a database session (e.g. dependency injection in web
# handlers).
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models to inherit from.
Base = declarative_base()
