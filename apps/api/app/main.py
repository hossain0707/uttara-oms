from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from .auth import Actor, current_actor
from .config import settings
from .database import get_db
from .routes import access, approvals, members, organization, reports

app = FastAPI(title="Uttara OMS API", version="0.1.0",
              docs_url=None if settings().environment == "production" else "/docs",
              redoc_url=None)

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
    db.execute(text("SELECT 1"))
    return {"status": "ready"}


@app.get("/api/v1/me")
def me(actor: Actor = Depends(current_actor)):
    return {"email": actor.email, "roles": [
        {"role": role, "scope_node_id": str(scope) if scope else None}
        for role, scope in actor.grants], "mfa": actor.mfa}
