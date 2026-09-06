"""统一 API 响应结构"""
from typing import Any, Dict, List, Optional

# 业务码
CODE_OK = 0
CODE_ERR = 1


def success(data: Any = None, msg: str = "ok", code: int = CODE_OK) -> Dict[str, Any]:
    return {"code": code, "msg": msg, "data": data}


def fail(msg: str = "error", code: int = CODE_ERR, data: Any = None) -> Dict[str, Any]:
    return {"code": code, "msg": msg, "data": data}


def paginated(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
    msg: str = "ok",
) -> Dict[str, Any]:
    """分页响应：data = {list, total, page, page_size, total_pages}"""
    total_pages = (total + page_size - 1) // page_size if page_size else 0
    return success(
        {
            "list": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
        },
        msg=msg,
    )


def page_offset(page: int, page_size: int) -> int:
    return (page - 1) * page_size


def clamp_page_size(page_size: int, default: int = 10, max_size: int = 100) -> int:
    if not page_size or page_size <= 0:
        return default
    return min(page_size, max_size)


def build_meta(total: Optional[int] = None) -> Dict[str, Any]:
    return {"total": total} if total is not None else {}
