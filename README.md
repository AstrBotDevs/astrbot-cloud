# AstrBot Cloud

AstrBot 项目的中心化 API 服务，提供 RESTful API 接口。

## 特性

- 🚀 基于 FastAPI 构建的高性能 API
- 📦 统一的响应格式 (code, msg, data)
- 🔄 RESTful API 设计风格
- 📖 自动生成的 API 文档
- 🌐 支持 CORS

## 技术栈

- Python 3.12+
- FastAPI
- httpx
- uvicorn

## 项目结构

```
astrbot-cloud/
├── app/
│   ├── __init__.py
│   ├── main.py                 # 应用入口
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── github.py       # GitHub API 路由
│   └── schemas/
│       ├── __init__.py
│       └── response.py         # 统一响应模型
├── pyproject.toml
└── README.md
```

## 安装依赖

```bash
uv sync
```

## 运行服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API 文档

启动服务后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 接口

### 统一响应格式

所有接口返回统一的 JSON 格式：

```json
{
  "code": 200,
  "msg": "success",
  "data": {}
}
```

- `code`: 状态码，200 表示成功
- `msg`: 响应消息
- `data`: 响应数据

### 当前可用接口

#### 1. 获取 AstrBot GitHub 仓库信息

```
GET /api/v1/github/repo-info
```

转发 GitHub API，获取 AstrBot 仓库的基本信息。

**响应示例：**

```json
{
  "code": 200,
  "msg": "获取仓库信息成功",
  "data": {
    "id": 123456,
    "name": "AstrBot",
    "full_name": "AstrBotDevs/AstrBot",
    "description": "...",
    "stargazers_count": 100,
    "forks_count": 20,
    ...
  }
}
```

## 开发

### 添加新接口

1. 在 `app/api/v1/` 下创建新的路由文件
2. 在 `app/api/v1/__init__.py` 中注册路由
3. 使用 `ApiResponse` 模型返回统一格式

示例：

```python
from fastapi import APIRouter
from app.schemas import ApiResponse

router = APIRouter()

@router.get("/example")
async def example():
    return ApiResponse.success(data={"hello": "world"})
```

## License

MIT
