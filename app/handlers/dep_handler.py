

import os
from typing import Annotated
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from handlers.db_handler import NoloUserDB
from models.jwt_model import TokenData
from models.iam_model import User, UserInDB
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


SECRET_KEY=os.getenv("JWT_SECRET_KEY")
REFRESH_KEY=os.getenv("JWT_REFRESH_SECRET_KEY")
ALGORITHM=os.getenv("JWT_ALGORITHM")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

user_ddb = os.getenv("USER_DDB_TABLE_NAME")

# Handlers
user_db = NoloUserDB()



async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = user_db.get_one_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user