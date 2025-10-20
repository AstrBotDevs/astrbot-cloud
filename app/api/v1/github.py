from fastapi import APIRouter
from typing import Any, Dict
import httpx

from app.schemas.response import ApiResponse

router = APIRouter()


@router.get("/repo-info", response_model=ApiResponse[Dict[str, Any]])
async def get_astrbot_repo_info():
    """
    获取 AstrBot GitHub 仓库的基本信息

    转发 GitHub API: https://api.github.com/repos/AstrBotDevs/AstrBot
    """
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
