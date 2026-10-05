# auth.py
# Handles password hashing and JWT creation/verification for login.

import os
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
import models

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
if os.getenv("QLMS_ENV") == "production" and (not SECRET_KEY or len(SECRET_KEY.encode()) < 32):
    raise ValueError("Production requires a strong SECRET_KEY of at least 32 bytes")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DUMMY_PASSWORD_HASH = bcrypt.hashpw(b"qlms-login-timing-only", bcrypt.gensalt()).decode()

# Tells FastAPI where the login route lives, for its auto-generated docs
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# Hashes a plain password before storing it in the database
def hash_password(password: str) -> str:
    if not password or len(password.encode("utf-8")) > 72:
        raise ValueError("Password must contain 1 to 72 UTF-8 bytes")
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# Checks a plain password against the stored hash at login time
def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or len(plain_password.encode("utf-8")) > 72:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except (ValueError, TypeError, AttributeError):
        return False


# Creates a signed token containing the user's id, role and current session version.
def create_access_token(user_id: int, role: str, token_version: int) -> str:
    issued_at = datetime.now(timezone.utc)
    expire = issued_at + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "ver": token_version,
        "iat": issued_at,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# Reads the token from the request and loads the matching user from the database.
# Any route that adds this as a dependency becomes a protected, login-required route.
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        token_version = payload.get("ver")
        if (
            not isinstance(user_id, str)
            or not user_id.isdigit()
            or not isinstance(token_version, int)
            or isinstance(token_version, bool)
        ):
            raise credentials_error
        user_id = int(user_id)
    except (jwt.PyJWTError, TypeError, ValueError):
        raise credentials_error

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if (
        user is None
        or not user.is_active
        or user.token_version != token_version
    ):
        raise credentials_error
    return user


# Restricts a route to owner accounts only
def require_owner(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required")
    return current_user
