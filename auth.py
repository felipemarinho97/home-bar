"""Authentication middleware for backoffice routes using HTTP Basic Auth."""

import os
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()


def check_backoffice(credentials: HTTPBasicCredentials = Depends(security)):
    """Validate backoffice password from environment variable."""
    correct_password = os.getenv("BACKOFFICE_PASSWORD")
    backend_username = os.getenv("BACKOFFICE_USERNAME", "admin")

    if not correct_password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server not configured with BACKOFFICE_PASSWORD",
        )

    username_ok = secrets.compare_digest(credentials.username, backend_username)
    password_ok = secrets.compare_digest(credentials.password, correct_password)

    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True
