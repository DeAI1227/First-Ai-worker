from __future__ import annotations

from fastapi import Header, HTTPException, Request, status


def require_api_token(request: Request, authorization: str | None = Header(default=None)) -> None:
    expected = str(getattr(request.app.state, "api_auth_token", "") or "").strip()
    if not expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API_AUTH_TOKEN is not configured")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    if token != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API token")
