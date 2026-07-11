"""Authentication dependencies (placeholder)."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
) -> dict:
    """Placeholder: resolve authenticated user from JWT."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    # Business logic to be implemented in a later phase.
    return {"token": credentials.credentials}


CurrentUser = Annotated[dict, Depends(get_current_user)]
