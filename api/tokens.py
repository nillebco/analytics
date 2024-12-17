from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .secrets import get_secret

SECRET_KEY = get_secret("jwt_signing_key")


def create_jwt_token(user_id: str, expires_delta: timedelta = timedelta(hours=1)):
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": user_id, "exp": expire.timestamp()}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload["exp"] < datetime.now(timezone.utc).timestamp():
            raise HTTPException(status_code=403, detail="Token has expired")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid token")
    return payload["sub"]
