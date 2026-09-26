from pydantic import BaseModel, ConfigDict


class SignUpRequest(BaseModel):
    username: str
    email: str
    password: str
    confirm_password: str


class SignInRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    model_config = ConfigDict(from_attributes=True)
