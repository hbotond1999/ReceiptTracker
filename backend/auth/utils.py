from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
import jwt
from fastapi import HTTPException, status
from sqlmodel import Session, select
from .models import User as DBUser, RefreshToken
import os
from dotenv import load_dotenv
from datetime import timezone

load_dotenv()

# Load RSA keys
KEYS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "keys")
PRIVATE_KEY_PATH = os.path.join(KEYS_DIR, "private_key.pem")
PUBLIC_KEY_PATH = os.path.join(KEYS_DIR, "public_key.pem")

with open(PRIVATE_KEY_PATH, "rb") as f:
    PRIVATE_KEY = f.read()
with open(PUBLIC_KEY_PATH, "rb") as f:
    PUBLIC_KEY = f.read()

ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))  # 1 óra fejlesztéshez
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, PRIVATE_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None, session: Session = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, PRIVATE_KEY, algorithm=ALGORITHM)
    # Store for rotation in DB
    if session and "sub" in data:
        user = get_user_by_username(session, data["sub"])
        if user:
            db_token = RefreshToken(token=encoded_jwt, user_id=user.id)
            session.add(db_token)
            session.commit()
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def is_refresh_token_valid(token: str, session: Session):
    return session.exec(select(RefreshToken).where(RefreshToken.token == token)).first() is not None

def rotate_refresh_token(old_token: str, data: dict, session: Session):
    # Invalidate old refresh token in DB
    db_token = session.exec(select(RefreshToken).where(RefreshToken.token == old_token)).first()
    if not db_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    session.delete(db_token)
    session.commit()
    # Generate new refresh token
    return create_refresh_token(data, session=session)

def get_user_by_username(session: Session, username: str):
    statement = select(DBUser).where(DBUser.username == username)
    result = session.exec(statement).first()
    return result 