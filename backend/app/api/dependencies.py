"""Common API dependencies"""
from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db


def get_database() -> Generator[Session, None, None]:
    """Get database session dependency"""
    return get_db()
