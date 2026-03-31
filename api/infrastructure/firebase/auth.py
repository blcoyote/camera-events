"""Firebase JWT authentication dependencies for FastAPI routes."""
from typing import Annotated, Any

import jwt
from fastapi import HTTPException, Header, Query
from fastapi.security import HTTPBearer
from firebase_admin import auth
from loguru import logger

bearer_scheme = HTTPBearer(auto_error=False)


def verify_token(token: str) -> dict[str, Any]:
    """
    Verify a Firebase ID token and return the decoded claims.

    Args:
        token: The Firebase ID token to verify.

    Returns:
        The decoded token claims dict.

    Raises:
        HTTPException: 401 if the token is missing, 403 if it is invalid.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        claims = auth.verify_id_token(token)
        logger.info(f"Successfully validated token for: {claims['email']}")
        return claims
    except (ValueError, jwt.exceptions.DecodeError):
        raise HTTPException(status_code=403, detail="Invalid token")
    except Exception as e:
        logger.error(f"AppCheckError: {e}")
        raise HTTPException(status_code=403, detail="Invalid token")


def verify_user_check(X_token: Annotated[str, Header()] = "") -> None:
    """FastAPI dependency: validate the ``X-Token`` request header."""
    verify_token(X_token)


def verify_url_token(token: Annotated[str | None, Query()] = None) -> None:
    """
    FastAPI dependency: validate a token passed as a URL query parameter.

    Used by download endpoints that generate shareable links.

    Args:
        token: The token from the query parameter.

    Raises:
        HTTPException: 401 if the token is absent, 403 if it is invalid.
    """
    if token is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    verify_token(token)
