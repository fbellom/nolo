"""
Identity and Access Manager
"""
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
import logging


# Create Logger
logger = logging.getLogger(__name__)


class NoloToken:
    """
    Token Manager
    """

    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY")
        self.refresh_key = os.getenv("JWT_REFRESH_SECRET_KEY")
        self.algorithm = os.getenv("JWT_ALGORITHM")
        self.token_expires = int(os.getenv("JWT_TOKEN_EXPIRES_MIN"))
        self.token_refresh = int(os.getenv("JWT_TOKEN_REFRESH_MIN"))
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        logger.info("Token Backend Object in Use")

    def verify_password(self, plain_pwd: str, hashed_pwd: str) -> bool:
        return self.pwd_context.verify(plain_pwd, hashed_pwd)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def create_access_token(
        self, data: dict, expires_delta: timedelta | None = None
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            # Token Expires after 30minutes
            expire = datetime.utcnow() + timedelta(minutes=self.token_expires)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(
        self, data: dict, expires_delta: timedelta | None = None
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.token_refresh)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.refresh_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def validate_refresh_token(self, token: str) -> dict | None:
        try:
            payload = jwt.decode(token, self.refresh_key,algorithms=[self.algorithm])
            return payload
        except JWTError:
            logger.error("Refresh token validation failed")
            return None
                
