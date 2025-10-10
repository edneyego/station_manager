from fastapi import APIRouter, Depends, HTTPException

from application.authenticate_user import AuthenticateUser
from application.controller.dependencies.authenticate_user_dependence import get_authenticate_user_uc
from application.controller.dependencies.token_response import TokenResponse
from application.controller.dependencies.user import User
from infrastructure.exceptions.auth_error import AuthError

router = APIRouter(prefix="/OAuth", tags=["OAuth"])

@router.post("/token", response_model=TokenResponse)
def login(
    form: User,
    uc: AuthenticateUser = Depends(get_authenticate_user_uc),
):
    try:
        return uc(form.user_name, form.password)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
