"""
Portfolio Backend API
======================
A small CMS-style backend for Muhammad Abdul Kareem's portfolio site.

Run locally with:
    uvicorn app.main:app --reload

Interactive API docs (auto-generated):
    http://127.0.0.1:8000/docs
"""
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .routers import (
    auth_router,
    hero_router,
    about_router,
    skills_router,
    experience_router,
    projects_router,
    contact_info_router,
    contact_messages_router,
)

logger = logging.getLogger("uvicorn.error")

# Create all tables on startup if they don't already exist.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Portfolio API",
    description="Backend API powering Muhammad Abdul Kareem's dynamic portfolio site.",
    version="1.0.0",
)

# CORS: allows the portfolio frontend (served from a different origin,
# e.g. GitHub Pages) to call this API from the browser. Restrict
# allow_origins to your real domain in production for tighter security.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Adds baseline security headers to every response — flagged by
    browser dev tools / security audits as missing otherwise.
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Catches any error that isn't already handled. Without this, an
    unhandled 500 can skip past CORSMiddleware's response headers
    entirely, which makes the browser misreport a totally unrelated
    backend bug as a "CORS policy" error — very confusing to debug blind.
    """
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
        headers={"Access-Control-Allow-Origin": request.headers.get("origin", "*")},
    )


# NOTE: uploaded photos are no longer served from local disk — they're
# stored on Cloudinary now (see app/cloudinary_utils.py), since
# serverless hosting has no reliable persistent local filesystem.

app.include_router(auth_router.router)
app.include_router(hero_router.router)
app.include_router(about_router.router)
app.include_router(skills_router.router)
app.include_router(experience_router.router)
app.include_router(projects_router.router)
app.include_router(contact_info_router.router)
app.include_router(contact_messages_router.router)


@app.get("/", tags=["Health"])
def root():
    """
    Health check endpoint. Also serves as the "warm-up ping" target —
    the frontend hits this first, before requesting real data, to
    trigger the serverless cold start early while a loading animation
    plays, rather than waiting on the actual data-fetch calls.
    """
    return {"status": "ok", "message": "Portfolio API is running. Visit /docs for documentation."}
