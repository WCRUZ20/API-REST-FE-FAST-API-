import json
import logging
import os
from typing import Optional

from fastapi import Request
from jwt import ExpiredSignatureError, InvalidTokenError, decode
from starlette.middleware.base import BaseHTTPMiddleware

from src.app.models.api_request_log import ApiRequestLog


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        try:
            user_identifier = self._get_user_identifier(request)
            response_detail = self._extract_response_detail(response)

            await ApiRequestLog.create(
                endpoint=request.url.path,
                method=request.method,
                response_code=response.status_code,
                response_detail=response_detail,
                user_identifier=user_identifier,
            )
        except Exception as error:
            logging.exception("No se pudo guardar el log de request/response: %s", error)

        return response

    def _get_user_identifier(self, request: Request) -> Optional[str]:
        authorization = request.headers.get("authorization")
        if not authorization:
            return None

        token_parts = authorization.split(" ")
        if len(token_parts) != 2 or token_parts[0].lower() != "bearer":
            return None

        secret = os.getenv("SECRET_KEY")
        if not secret:
            return None

        token = token_parts[1]
        try:
            payload = decode(token, key=secret, algorithms=["HS256"])
            return str(payload.get("usuario") or payload.get("full_name") or payload.get("id") or "") or None
        except (ExpiredSignatureError, InvalidTokenError):
            return None

    def _extract_response_detail(self, response) -> Optional[str]:
        body = getattr(response, "body", None)
        if body is None:
            return None

        body_str = body.decode("utf-8", errors="ignore")
        if not body_str:
            return None

        try:
            parsed = json.loads(body_str)
            if isinstance(parsed, dict):
                detail = parsed.get("detail") or parsed.get("message") or parsed
            else:
                detail = parsed
        except json.JSONDecodeError:
            detail = body_str

        detail_as_str = detail if isinstance(detail, str) else json.dumps(detail, ensure_ascii=False)
        return detail_as_str[:2000]
