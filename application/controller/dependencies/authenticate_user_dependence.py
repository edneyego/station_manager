from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from application.authenticate_user import AuthenticateUser
from infrastructure.auth.jwt_bearer import JWTAuthProvider
from infrastructure.auth.jwt_handler import JWTAuthenticator
from infrastructure.exceptions.auth_error import AuthError


def get_authenticate_user_uc() -> AuthenticateUser:
    token_provider = JWTAuthProvider()
    authenticator = JWTAuthenticator(token_provider)
    return AuthenticateUser(authenticator)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    token = credentials.credentials
    provider = JWTAuthProvider()

    try:
        payload = provider.verify_token(token)
        return payload  # Pode ser dict ou objeto de domínio
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)