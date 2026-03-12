import json
import os
from fastapi import APIRouter

router = APIRouter()

DATA_FILE = "data/announcement.json"


@router.get("")
async def get_announcement():
    """获取公告信息"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {"code": 200, "message": "success", "data": data}
    except Exception:
        pass

    return {
        "code": 200,
        "message": "success",
        "data": {"notice": {}},
    }
