from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from .auth import Actor, account_actor, bearer, jwt_claims
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from .models import AppUser, AuditLog
from .config import settings
from .database import get_db
from .routes import access, approvals, members, organization, reports, personal

app = FastAPI(title="Uttara OMS API", version="0.1.0",
              docs_url=None if settings().environment == "production" else "/docs",
              redoc_url=None, openapi_url=None if settings().environment == "production" else "/openapi.json")

app.add_middleware(CORSMiddleware, allow_origins=settings().allowed_origins,
                   allow_credentials=False, allow_methods=["GET", "POST", "PATCH", "PUT"],
                   allow_headers=["Authorization", "Content-Type"],
                   expose_headers=["Content-Disposition"])

app.include_router(personal.router, prefix="/api/v1")
app.include_router(access.router, prefix="/api/v1")
app.include_router(members.router, prefix="/api/v1")
app.include_router(organization.router, prefix="/api/v1")
app.include_router(approvals.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/health/ready")
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        version = db.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
        if version != "0005_personal_workspace":
            return JSONResponse(status_code=503, content={"status": "not_ready"})
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready"}


@app.get("/api/v1/me")
def me(actor: Actor = Depends(account_actor)):
    return {"id": str(actor.id), "email": actor.email, "roles": [
        {"role": role, "scope_node_id": str(scope) if scope else None}
        for role, scope in actor.grants], "mfa": actor.mfa}


@app.post("/api/v1/account/register")
def register_account(credentials: HTTPAuthorizationCredentials = Depends(bearer),
                     db: Session = Depends(get_db)):
    """Idempotent basic account registration; never assigns organizational access."""
    claims = jwt_claims(credentials.credentials)
    try:
        subject = str(UUID(claims["sub"]))
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(401, "Invalid account identity") from exc
    # app_metadata is managed by Auth; user_metadata is user editable and is not trusted.
    email = claims.get("email")
    metadata = claims.get("app_metadata")
    if (not isinstance(metadata, dict) or metadata.get("provider") not in {"google", "email"}
            or claims.get("is_anonymous") is True or not isinstance(email, str)
            or len(email) > 320 or email.count("@") != 1):
        raise HTTPException(403, "Verified email or Google sign-in is required for registration")
    user = db.query(AppUser).filter(AppUser.auth_sub == subject).first()
    if user is None:
        try:
            with db.begin_nested():
                user = AppUser(auth_sub=subject, email=email, active=True)
                db.add(user)
                db.flush()
                db.add(AuditLog(actor_id=user.id, action="ACCOUNT_REGISTERED",
                                target_id=str(user.id), detail="Verified basic account; no organizational role"))
                db.flush()
            db.commit()
        except IntegrityError:
            db.rollback()
            user = db.query(AppUser).filter(AppUser.auth_sub == subject).first()
            if user is None:
                raise HTTPException(409, "Account registration conflict; retry")
    if not user.active:
        raise HTTPException(403, "Account is disabled")
    return {"registered": True}


@app.middleware("http")
async def secure_responses(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    # Pydantic errors otherwise echo input (including personal fields and tokens).
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]})
