import os
from datetime import datetime, timedelta
from jose import JWTError, jwt

SECRET = os.environ.get("WMS_JWT_SECRET") or os.environ.get("WMS_COOKIE_SECRET") or "wms-api-dev"
ALGORITHM = "HS256"
EXPIRES_HOURS = 24 * 7

def create_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=EXPIRES_HOURS)
    return jwt.encode({"sub": email, "exp": expire}, SECRET, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
