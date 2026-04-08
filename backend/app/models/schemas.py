from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    code: str
    new_password: str


class TokenResponse(BaseModel):
    token: str
    user: dict


class SolveTextRequest(BaseModel):
    expression: str


class SolveResult(BaseModel):
    expression: str
    parsed: str
    solution: Dict[str, Any]
    steps: List[str]
    type: str
    confidence: float
