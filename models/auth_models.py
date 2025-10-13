from pydantic import BaseModel, EmailStr
from enum import Enum

class UserRole(str, Enum):
    user = "user"
    recruiter = "recruiter"
    admin = "admin"

class SignUpRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.user

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role : UserRole