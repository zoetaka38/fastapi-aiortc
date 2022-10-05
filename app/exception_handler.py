import logging
from dataclasses import dataclass
from typing import Mapping

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

DEFAULT_DEVELOPER_MESSAGE = ""
DEFAULT_CODE = "000"

logger = logging.getLogger(__name__)


def init_app(app: FastAPI) -> None:
    # 例外ハンドラの登録
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(404, not_found_handler)


@dataclass(frozen=True)
class Error:
    developer_message: str = ""
    code: str = "000"

    def to_response(self) -> Mapping:
        return {
            "code": self.code,
            "developer_message": self.developer_message,
        }


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """リクエストパラメータのバリデーションエラーハンドラー"""
    logger.info(exc)
    errors = [Error(developer_message=str(exc))]
    return JSONResponse(
        status_code=400, content={"errors": [error.to_response() for error in errors]}
    )


async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """404のエラーハンドラー"""
    error = Error(
        developer_message="Not found",
        code=DEFAULT_CODE,
    )
    return JSONResponse(status_code=404, content={"errors": [error.to_response()]})
