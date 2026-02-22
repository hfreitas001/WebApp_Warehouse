"""Dependências: usuário atual via JWT (só lê do WebApp.auth)."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from api.auth_jwt import decode_token

security = HTTPBearer(auto_error=False)


def _get_user_row(email: str):
    from WebApp.auth.auth import get_user
    return get_user(email)


def get_current_user_email(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    if not creds or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = decode_token(creds.credentials)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return email


def get_current_user(email: str = Depends(get_current_user_email)):
    user = _get_user_row(email)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user
