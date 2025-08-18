from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash_password(p: str) -> str:
    return pwd_context.hash(p)
def verify_password(p: str, h: str) -> bool:
    return pwd_context.verify(p, h)
def create_jwt(sub: str, secret: str, minutes: int):
    payload = {"sub": sub, "exp": datetime.now(timezone.utc) + timedelta(minutes=minutes), "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, secret, algorithm="HS256")