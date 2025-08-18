from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any
from datetime import datetime
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
class LoginIn(BaseModel):
    email: EmailStr
    password: str
class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    name: str
class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    is_superadmin: bool
    class Config:
        from_attributes = True
class WatchAddIn(BaseModel):
    symbols: List[str]
class EmailAddIn(BaseModel):
    emails: List[EmailStr]
class PortfolioIn(BaseModel):
    symbol: str
    qty: float
    avg_price: float
class SignalOut(BaseModel):
    symbol: str
    technique: str
    action: str
    buy_price: float
    stop_loss: float
    asof: datetime
    meta: Dict[str, Any]