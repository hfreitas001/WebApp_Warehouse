"""Admin: lê/usa WebApp.auth (list_pending, approve_user, etc.) sem alterar arquivos auth."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import get_current_user

router = APIRouter()


def _require_admin(user):
    from WebApp.auth.auth import can_access_module
    if not can_access_module(user, "admin_usuarios"):
        raise HTTPException(status_code=403, detail="Sem permissão")


@router.get("/users/pending")
def list_pending(user=Depends(get_current_user)):
    _require_admin(user)
    from WebApp.auth.auth import list_pending_users
    df = list_pending_users()
    return df.to_dict(orient="records")


class ApproveBody(BaseModel):
    email: str


@router.post("/users/approve")
def approve(body: ApproveBody, user=Depends(get_current_user)):
    _require_admin(user)
    from WebApp.auth.auth import approve_user
    approve_user(body.email.strip(), user.get("email") or "api")
    return {"ok": True}


@router.get("/users")
def list_all(user=Depends(get_current_user)):
    _require_admin(user)
    from WebApp.auth.auth import TABLE_USERS
    from WebApp.core.utils import get_bq_client
    from google.cloud import bigquery
    import json
    client = get_bq_client()
    q = f"SELECT email, role, allowed_modules, approved_at, approved_by, last_login FROM `{TABLE_USERS}` ORDER BY email"
    df = client.query(q).to_dataframe()
    return df.to_dict(orient="records")


class UpdateModulesBody(BaseModel):
    email: str
    allowed_modules: list[str]


@router.put("/users/modules")
def update_modules(body: UpdateModulesBody, user=Depends(get_current_user)):
    _require_admin(user)
    import json
    from WebApp.auth.auth import TABLE_USERS
    from google.cloud import bigquery
    from WebApp.core.utils import get_bq_client
    client = get_bq_client()
    q = f"UPDATE `{TABLE_USERS}` SET allowed_modules = @mods WHERE LOWER(TRIM(email)) = LOWER(TRIM(@email))"
    client.query(q, job_config=bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("mods", "STRING", json.dumps(body.allowed_modules)),
            bigquery.ScalarQueryParameter("email", "STRING", body.email.strip()),
        ]
    )).result()
    return {"ok": True}
