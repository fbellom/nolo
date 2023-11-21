"""
Identity and Access Manager
"""
from typing import Annotated
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from models.iam_model import UserInDB, User
from models.jwt_model import TokenData

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm



class NoloIAM:
    """
    Identity and Access Manager
    """

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

    def __init__(self, user_db=None):
        self.secret_key = os.getenv("JWT_SECRET_KEY")
        self.algorithm = os.getenv("JWT_ALGORITHM")
        self.token_expires = int(os.getenv("JWT_TOKEN_EXPIRES_MIN"))
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.oauth2_scehme = OAuth2PasswordBearer(tokenUrl="token")
        self.user_db = user_db


    def verify_password(self,plain_pwd, hashed_pwd):
        return self.pwd_context.verify(plain_pwd, hashed_pwd)  

    def get_password_hash(self,password):
        return self.pwd_context.hash(password)  
    
    def get_user(self, username:str):
        if username in self.user_db:
            user_dict = self.user_db[username]
            return UserInDB(**user_dict)
        
    def authenticate_user(self,username: str, password: str):
        user = self.get_user(username)
        if not user:
            return False
        if not self.verify_password(password, user.hashed_password):
            return False
        return user
    
    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            # Token Expires after 30minutes
            expire = datetime.utcnow() + timedelta(minutes=self.token_expires)    

        to_encode.update({"exp" : expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)  
        return encoded_jwt  
    
    
    async def get_current_user(self,token: Annotated[str, Depends(oauth2_scheme)]):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not Validate credentials",
            headers={"WWW-Authenticate" : "Bearer"}
        )
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except JWTError:
            raise credentials_exception
        user = self.get_user(db=self.user_db, username=token_data.username)  
        if user is None:
            raise credentials_exception
        return user



    async def get_current_active_user(self, current_user: Annotated[User, Depends(get_current_user)]):
        if current_user.disabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Active User"
            )    

