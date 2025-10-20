from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一的 API 响应模型"""

    code: int = Field(default=200, description="响应状态码，200 表示成功，其他表示错误")
    msg: str = Field(default="success", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")

    class Config:
        json_schema_extra = {"example": {"code": 200, "msg": "success", "data": {}}}

    @classmethod
    def success(cls, data: Any = None, msg: str = "success") -> "ApiResponse":
        """成功响应"""
        return cls(code=200, msg=msg, data=data)

    @classmethod
    def error(
        cls, code: int = 500, msg: str = "error", data: Any = None
    ) -> "ApiResponse":
        """错误响应"""
        return cls(code=code, msg=msg, data=data)
