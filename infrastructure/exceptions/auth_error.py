class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code


class ForbiddenError(AuthError):
    def __init__(self, message: str = "Acesso negado"):
        super().__init__(message, status_code=403)

class TokenExpiredError(AuthError):
    def __init__(self, message: str = "Token expirado"):
        super().__init__(message, status_code=401)
