from fastapi import APIRouter,HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

# Module specific Libraries
from models.iam_model import User
from models.jwt_model import Token, TokenData
from handlers.iam_handler import NoloIAM

# Global Vars
MODULE_NAME="token"
MODULE_PREFIX="/token"
MODULE_TAGS=[MODULE_NAME]

# FastAPI Instance
router = APIRouter(
    prefix=MODULE_PREFIX,
    tags=MODULE_TAGS
)



# Models
user_db = {
    "admin" : {
        "username" : "admin",
        "full_name" : "admin",
        "email" : "admin@local.xyz",
        "hashed_password" : "$2b$12$cPo7FUczCVOwMFTWH3A.v.E1CxxKeH516Xg4M42vfs8A4Jo0DIZiO",
        "disabled" : False,
    }
}
    
# Handlers
iam = NoloIAM(user_db=user_db)

# Environment



#Routes
@router.post("", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = iam.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate" : "Bearer"}
        )
    access_token = iam.create_access_token(
        data={"sub" : user.username}
    )

    return {"access_token" : access_token, "token_type" : "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(iam.get_current_active_user)]
):
    return current_user