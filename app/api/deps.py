from typing import Generator, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

import jwt
from jwt.exceptions import PyJWTError
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.models.user import User
from app.core.config import settings

# Cookie name for auth token
COOKIE_NAME = "access_token"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)


class TokenData(BaseModel):
    email: Optional[str] = None


def get_token_from_request(request: Request, header_token: Optional[str] = None) -> Optional[str]:
    """
    Extract token from Authorization header or cookie.
    Priority: Header > Cookie
    """
    # First try header (from OAuth2PasswordBearer)
    if header_token:
        return header_token

    # Then try cookie
    cookie_token = request.cookies.get(COOKIE_NAME)
    if cookie_token:
        return cookie_token

    return None


def get_current_user(
    request: Request,
    header_token: Optional[str] = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    """
    Get current user from JWT token (header or cookie).
    """
    token = get_token_from_request(request, header_token)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except PyJWTError:
        raise credentials_exception

    user = session.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_user_optional(
    request: Request,
    header_token: Optional[str] = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.
    Useful for endpoints that work for both authenticated and anonymous users.
    """
    token = get_token_from_request(request, header_token)

    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        user = session.query(User).filter(User.email == email).first()
        return user
    except PyJWTError:
        return None

