from typing import Annotated
from fastapi import HTTPException, Header, Query
from fastapi.security import HTTPBearer
from firebase_admin import auth
import jwt
from loguru import logger

bearer_scheme = HTTPBearer(auto_error=False)


def verify_token(token: str) -> dict:
    """
    Verifies a Firebase ID token and returns the decoded claims if valid.
    Args:
        token (str): The Firebase ID token to verify.
    Returns:
        dict: The decoded token claims.
    Raises:
        HTTPException: If the token is missing or invalid.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        auth_check_claims = auth.verify_id_token(token)
        logger.info(f"successfully validated token for: {auth_check_claims['email']}")
        return auth_check_claims
    except (ValueError, jwt.exceptions.DecodeError):
        # Token is invalid, forbidden
        raise HTTPException(status_code=403, detail="Invalid token")
    except Exception as e:
        # Token is invalid, forbidden
        logger.error(f"AppCheckError: {e}")
        raise HTTPException(status_code=403, detail="Invalid token")


def verify_user_check(X_token: Annotated[str, Header()] = "") -> None:
    verify_token(X_token)


def verify_url_token(token: Annotated[str | None, Query()]) -> None:
    """
    Dependency to verify a token passed as a query parameter.

    Args:
        token (str | None): The token from the query parameter.

    Raises:
        HTTPException: If the token is missing or invalid.
    """
    if token is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    verify_token(token)
