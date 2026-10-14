from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class StandardResponse(BaseModel, Generic[DataT]):
    success: bool = True
    data: Optional[DataT] = None
    error: Optional[ErrorDetail] = None


def success_response(data: Any = None) -> dict:
    return {
        "success": True,
        "data": data,
        "error": None
    }


def error_response(code: str, message: str, details: Any = None) -> dict:
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        }
    }
