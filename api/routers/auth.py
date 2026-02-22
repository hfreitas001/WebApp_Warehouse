"""Auth: login (usa WebApp.auth), me (lê usuário)."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from api.auth_jwt import create_token
from api.deps import get_current_user_email

router = APIRouter()


class LoginBody(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    email: str
    role: str
    allowed_modules: list[str]
    approved_at: str | None


def _user_to_out(user):
    import json
    import pandas as pd
    raw = user.get("allowed_modules")
    try:
        mods = json.loads(raw) if isinstance(raw, str) else (raw or [])
    except Exception:
        mods = []
    approved = user.get("approved_at")
    approved_at = None if (approved is None or pd.isna(approved)) else str(approved)
    return UserOut(
        email=str(user.get("email", "")),
        role=str(user.get("role") or "user"),
        allowed_modules=mods,
        approved_at=approved_at,
    )


@router.post("/login")
def login(body: LoginBody):
    from WebApp.auth.auth import login as auth_login, get_user
    ok, msg = auth_login(body.email.strip(), body.password)
    if not ok:
        raise HTTPException(status_code=401, detail=msg)
    user = get_user(body.email.strip())
    if user is None:
        raise HTTPException(status_code=500, detail="Erro ao carregar usuário")
    token = create_token(body.email.strip().lower())
    return {"access_token": token, "token_type": "bearer", "user": _user_to_out(user)}


@router.get("/me", response_model=UserOut)
def me(user=Depends(get_current_user_email)):
    from WebApp.auth.auth import get_user
    row = get_user(user)
    if row is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return _user_to_out(row)
