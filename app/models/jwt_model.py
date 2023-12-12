from pydantic import BaseModel


# JWT AUthentication OAUTH Model
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
