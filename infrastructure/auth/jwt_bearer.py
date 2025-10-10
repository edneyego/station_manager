import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from dotenv import load_dotenv
from fastapi import HTTPException

from domain.ports.auth_port import AuthTokenProvider
from infrastructure.settings.settings import get_settings

class JWTAuthProvider(AuthTokenProvider):

    def __init__(self):
        self.s = get_settings()
        self.SECRET_KEY = self.s.user_password
        self.ALGORITHM = "HS256"

    def create_access_token(self, data: dict, expires_delta: timedelta) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def verify_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
        except JWTError:
            raise HTTPException(status_code=401, detail="Token inválido ou expirado")
