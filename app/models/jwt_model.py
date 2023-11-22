from pydantic import BaseModel


# JWT AUthentication OAUTH Model
class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str


class TokenData(BaseModel):
    username: str | None = None
