import os
from fastapi import APIRouter

router = APIRouter()

DATA_DIR = "data/announcement"


@router.get("")
async def get_announcement():
    """获取公告信息，支持按语言包加载 Markdown 格式的 welcome_page"""

    base_data = {"notice": {"welcome_page": {}}}

    try:
        if os.path.exists(DATA_DIR):
            for file_name in os.listdir(DATA_DIR):
                if file_name.startswith("welcome_page.") and file_name.endswith(".md"):
                    # 提取 locale, 例如 welcome_page.zh-CN.md -> zh-CN
                    locale = file_name[len("welcome_page.") : -len(".md")]
                    file_path = os.path.join(DATA_DIR, file_name)
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            base_data["notice"]["welcome_page"][locale] = content
    except Exception:
        pass

    return {
        "code": 200,
        "message": "success",
        "data": base_data,
    }
