"""
Security dependencies for FastAPI route protection.
API Key Authentication
"""

import os
import logging

from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

logger = logging.getLogger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> None:
    """
    Validate the X-API-Key header against the API_SECRET_KEY environment variable.

    Set the key on Heroku:
        heroku config:set API_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))") --app vedi-backend

    Raises:
        HTTPException 403: if the key is missing or does not match.
    """
    expected_key = os.environ.get("API_SECRET_KEY")

    if not expected_key:
        # If no key is configured (local dev without env set), allow through
        # but log a warning so it's visible in logs.
        logger.warning(
            "API_SECRET_KEY is not set. All requests are unauthenticated. "
            "Set this environment variable in production."
        )
        return

    if not api_key or api_key != expected_key:
        logger.warning("Rejected request with invalid or missing X-API-Key header.")
        raise HTTPException(status_code=403, detail="Forbidden: invalid or missing API key.")
