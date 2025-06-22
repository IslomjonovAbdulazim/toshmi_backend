from pydantic import BaseModel

class LoginRequest(BaseModel):
    phone: int
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: str = None