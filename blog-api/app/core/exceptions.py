"""业务异常 + 全局异常处理"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.response import CODE_ERR, fail

logger = logging.getLogger("bluemoon")


class BizException(Exception):
    """业务异常：用于主动抛出的可预期错误"""

    def __init__(self, msg: str = "操作失败", code: int = CODE_ERR, status_code: int = 400):
        self.msg = msg
        self.code = code
        self.status_code = status_code
        super().__init__(msg)


class NotFoundException(BizException):
    def __init__(self, msg: str = "资源不存在"):
        super().__init__(msg=msg, code=404, status_code=404)


class AuthException(BizException):
    def __init__(self, msg: str = "未登录或登录已过期"):
        super().__init__(msg=msg, code=401, status_code=401)


class ForbiddenException(BizException):
    def __init__(self, msg: str = "没有权限执行该操作"):
        super().__init__(msg=msg, code=403, status_code=403)


class ConflictException(BizException):
    def __init__(self, msg: str = "数据冲突"):
        super().__init__(msg=msg, code=409, status_code=409)


class TooManyRequestsException(BizException):
    def __init__(self, msg: str = "操作过于频繁，请稍后再试"):
        super().__init__(msg=msg, code=429, status_code=429)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BizException)
    async def biz_exception_handler(request: Request, exc: BizException):
        logger.warning("BizException %s %s -> %s", request.method, request.url.path, exc.msg)
        return JSONResponse(
            status_code=exc.status_code,
            content=fail(msg=exc.msg, code=exc.code),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=fail(msg=str(exc.detail), code=exc.status_code),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        first = errors[0] if errors else {}
        loc = ".".join(str(x) for x in first.get("loc", [])[1:]) or "参数"
        msg = f"{loc} {first.get('msg', '参数校验失败')}"
        return JSONResponse(status_code=422, content=fail(msg=msg, code=422))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content=fail(msg="服务器内部错误", code=500))
