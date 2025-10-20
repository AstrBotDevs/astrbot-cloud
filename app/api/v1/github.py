from fastapi import APIRouter
from typing import Any, Dict, Optional
import httpx
from datetime import datetime, timedelta

from app.schemas.response import ApiResponse

router = APIRouter()

# 缓存数据结构
_cache: Dict[str, Dict[str, Any]] = {}


def get_cached_data(
    cache_key: str, cache_duration_hours: int = 1
) -> Optional[Dict[str, Any]]:
    """
    获取缓存数据

    Args:
        cache_key: 缓存键
        cache_duration_hours: 缓存时长（小时）

    Returns:
        缓存的数据，如果过期或不存在则返回 None
    """
    if cache_key in _cache:
        cache_entry = _cache[cache_key]
        cache_time = cache_entry.get("timestamp")
        if cache_time and datetime.now() - cache_time < timedelta(
            hours=cache_duration_hours
        ):
            return cache_entry.get("data")
    return None


def set_cached_data(cache_key: str, data: Any) -> None:
    """
    设置缓存数据

    Args:
        cache_key: 缓存键
        data: 要缓存的数据
    """
    _cache[cache_key] = {"timestamp": datetime.now(), "data": data}


@router.get("/repo-info", response_model=ApiResponse[Dict[str, Any]])
async def get_astrbot_repo_info():
    """
    获取 AstrBot GitHub 仓库的基本信息

    转发 GitHub API: https://api.github.com/repos/AstrBotDevs/AstrBot

    缓存时长: 1 小时
    """
    cache_key = "astrbot_repo_info"

    # 尝试从缓存获取数据
    cached_data = get_cached_data(cache_key, cache_duration_hours=1)
    if cached_data is not None:
        return ApiResponse.success(data=cached_data, msg="获取仓库信息成功（缓存）")

    github_api_url = "https://api.github.com/repos/AstrBotDevs/AstrBot"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                github_api_url,
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "AstrBot-Cloud",
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                data = response.json()
                # 缓存成功的响应数据
                set_cached_data(cache_key, data)
                return ApiResponse.success(data=data, msg="获取仓库信息成功")
            else:
                return ApiResponse.error(
                    code=response.status_code,
                    msg=f"GitHub API 返回错误: {response.status_code}",
                    data=None,
                )

    except httpx.TimeoutException:
        return ApiResponse.error(code=504, msg="请求 GitHub API 超时")
    except httpx.RequestError as e:
        return ApiResponse.error(code=503, msg=f"请求 GitHub API 失败: {str(e)}")
    except Exception as e:
        return ApiResponse.error(code=500, msg=f"服务器内部错误: {str(e)}")
