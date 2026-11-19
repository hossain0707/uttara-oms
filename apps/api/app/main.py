from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from .auth import Actor, current_actor
from .config import settings
from .database import get_db
from .routes import access, approvals, members, organization, reports

app = FastAPI(title="Uttara OMS API", version="0.1.0",
              docs_url=None if settings().environment == "production" else "/docs",
              redoc_url=None, openapi_url=None if settings().environment == "production" else "/openapi.json")

app.add_middleware(CORSMiddleware, allow_origins=settings().allowed_origins,
                   allow_credentials=False, allow_methods=["GET", "POST", "PATCH"],
                   allow_headers=["Authorization", "Content-Type"],
                   expose_headers=["Content-Disposition"])

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
        if version != "0004_invariants":
            return JSONResponse(status_code=503, content={"status": "not_ready"})
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready"}


@app.get("/api/v1/me")
def me(actor: Actor = Depends(current_actor)):
    return {"id": str(actor.id), "email": actor.email, "roles": [
        {"role": role, "scope_node_id": str(scope) if scope else None}
        for role, scope in actor.grants], "mfa": actor.mfa}


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
