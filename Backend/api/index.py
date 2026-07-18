"""
Vercel serverless entry point.

Vercel's Python runtime (@vercel/python) looks for an ASGI-compatible
`app` object in this file — it doesn't run `uvicorn` itself, Vercel's
own infrastructure handles that. This file just needs to expose the
real FastAPI app so Vercel can find and run it.

This file is NOT used for local development — use `uvicorn app.main:app
--reload` from the project root for that instead, as documented in the
README.
"""
import sys
import os

# Ensure the project root (one level up from /api) is importable, so
# `from app.main import app` works the same way it does locally.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app  # noqa: E402  (import after sys.path fix, intentional)
