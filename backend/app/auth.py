# [backend/app/auth.py]

import os
import logging
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # <--- [Change 1] 변경
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
# 1. Load environment variables
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY or SECRET_KEY == "default-unsafe-key":
    error_msg = "FATAL: SECRET_KEY environment variable is not set or is unsafe"
    logger.critical(error_msg)
    raise ValueError(error_msg)

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", 24))

# [Change 2] Use HTTPBearer instead of OAuth2PasswordBearer
# This allows a simple "Paste Token" input in Swagger UI
security = HTTPBearer()


def create_access_token(data: dict):
    """
    Generate a JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# [Change 3] Update dependency to use HTTPBearer
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify the JWT token from the request header (Authorization: Bearer <token>)
    """
    token = credentials.credentials  # Extract token string from "Bearer <token>"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id = int(payload.get("user_id"))
        room_id = int(payload.get("room_id"))

        if user_id is None or room_id is None:
            raise credentials_exception

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception

    except (TypeError, ValueError):
        raise credentials_exception