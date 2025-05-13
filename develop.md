# 开发日志与项目结构

## 1. 项目结构说明

```
A_Share_investment_Agent/
├── backend/                     # 后端 API 和服务
│   ├── dependencies.py          # 依赖注入 (如 LogStorage)
│   ├── main.py                  # FastAPI 应用实例
│   ├── models/                  # API 请求/响应模型 (Pydantic)
│   ├── routers/                 # 路由定义（API端点）
│   ├── schemas.py               # 内部数据结构/日志模型 (Pydantic)
│   ├── services/                # 业务逻辑服务
│   ├── state.py                 # 内存状态管理 (api_state)
│   ├── storage/                 # 日志存储实现
│   └── utils/                   # 后端工具函数
├── src/                         # Agent 核心逻辑和工具
│   ├── agents/                  # Agent 定义和工作流
│   ├── data/                    # 数据存储目录 (本地缓存等)
│   ├── tools/                   # 工具和功能模块 (LLM, 数据获取)
│   ├── utils/                   # 通用工具函数
│   ├── backtester.py            # 回测系统
│   └── main.py                  # Agent 工作流定义和命令行入口
├── logs/                        # 日志文件目录
├── web.py                       # Streamlit 前端交互页面
├── run_with_backend.py          # 启动后端并可选执行分析的脚本
├── pyproject.toml               # Poetry项目配置
├── poetry.lock                  # Poetry依赖锁定文件
├── .env/.env.example            # 环境变量配置
├── README.md                    # 项目文档
├── develop.md                   # 开发日志与结构说明
```

## 2. 主要开发变更日志

- 初始化项目结构，支持多智能体A股分析与决策。
- 实现 FastAPI 后端，支持异步分析任务、状态查询、结果获取等API。
- 增加 Streamlit 前端（web.py），支持股票代码输入、进度条、决策与多智能体结果展示、调试日志输出。
- 支持 Gemini/OpenAI LLM API，环境变量可配置。
- 增加调试日志区域，便于前端排查后端API调用与异常。
- 兼容 Windows/Ubuntu 部署，推荐使用 Poetry 管理依赖。
- 迁移准备：打包上传GitHub，准备在Ubuntu服务器部署。

## 3. 迁移/部署注意事项

- 推荐在 Ubuntu 22.04+ 环境下部署。
- 安装 Python 3.10+，建议用 pyenv 管理多版本。
- 安装 Poetry：`pip install poetry`
- 克隆仓库后，执行 `poetry install` 安装依赖。
- 配置 `.env` 文件，填写 Gemini/OpenAI API Key。
- 安装 akshare：`poetry add akshare`（如未自动安装）。
- 启动后端：`poetry run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`
- 启动前端：`poetry run streamlit run web.py`
- 如遇依赖或权限问题，优先检查虚拟环境、依赖包和API Key。

---

如有新功能开发、结构调整或部署经验，请持续补充本 develop.md。
