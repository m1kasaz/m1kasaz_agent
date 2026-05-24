# m1kasaz_agent

一个基于 **LangGraph + Python** 的个人 Agent 项目。

目标不是只做单次问答，而是逐步构建一个**可持续运行、可记忆用户偏好、可调度任务、可调用工具**的智能体系统。

当前仓库刚完成初始化，README 先用于明确方向、MVP 范围和后续演进路径。

## 项目目标

这个项目计划围绕以下核心能力展开：

- 多轮对话与线程级上下文管理
- 用户偏好与长期记忆
- PDF / DOCX 文档解析、转换、摘要与问答
- 每日 AI 论文推荐
- 基于用户兴趣的个性化推荐
- 后续扩展搜索、提醒、订阅、知识库等能力

## 为什么选择 LangGraph

相比单次调用式 Agent，这个项目更适合使用 LangGraph 做编排，原因主要有：

- 需要状态管理：保存消息、用户画像、工具结果和任务上下文
- 需要任务路由：聊天、文档处理、论文推荐会走不同流程
- 需要持久化：支持长流程、异步任务和可恢复执行
- 需要定时任务：每日推荐天然适合调度系统驱动
- 需要可扩展性：后续可以逐步拆成多个 subgraph 或角色节点

## 规划中的三层架构

1. **交互层**：CLI / Web / Bot / API
2. **编排层**：LangGraph 负责状态、路由、流程编排与持久化
3. **能力层**：文档转换、推荐、记忆、搜索、通知等工具服务

## MVP 范围

第一阶段优先跑通最小闭环：

- 支持自然语言输入并完成意图识别
- 支持基础文档处理：
  - `docx -> pdf`
  - `pdf -> text`
  - `docx -> text`
- 支持文档摘要与问答
- 支持每日推荐 1 篇 AI 论文
- 支持记录用户兴趣偏好与推荐历史
- 使用本地存储完成最小持久化

## 计划中的核心子流程

### 1. Chat

负责普通问答、上下文承接和统一响应生成。

### 2. Document

负责文件校验、格式识别、转换、文本提取，以及摘要 / QA。

### 3. Paper Recommendation

负责读取用户兴趣、拉取候选论文、打分排序、生成推荐摘要，并避免重复推荐。

## 推荐技术栈

### 后端

- Python 3.11+
- LangGraph
- LangChain Core
- FastAPI
- Pydantic

### 存储

- MVP：SQLite + 本地文件存储
- 进阶：Postgres / Redis / 对象存储
- 语义检索：pgvector / Chroma / Milvus

### 调度与通知

- MVP：APScheduler
- 进阶：Celery + Redis
- 通知渠道：邮件、飞书机器人、Web 通知

## 当前仓库状态

当前仓库仍处于初始化阶段，代码主体尚未落地，但已经有一些环境与插件配置。

### 配置体系说明

当前仓库中的 Agent 相关配置，统一按两套体系理解和维护。

#### 1. MCP 工具接入体系

这套体系解决“Claude 能连接哪些外部工具服务”的问题。

对应文件：

- `.mcp.json`

当前已接入：

- `lark-docs`：飞书文档导出 / 导入
- `tika`：文档检索与问答能力

后续如果新增 MCP，统一按下面格式在 README 中补充：

- `mcp-name`：一句话说明这个 MCP 提供什么能力

#### 2. AI 插件依赖体系

这套体系解决“项目依赖了哪些 AI 插件，以及实际锁定到哪些插件版本”的问题。

对应文件：

- `ai-plugin.json`：插件依赖声明
- `ai-plugin-lock.json`：插件依赖锁定结果

当前声明的插件包：

- `ttadk/backend`

当前锁定并展开的插件包括：

- `ttadk/core`
- `ttadk/gdp`
- `ttadk/hertz`
- `ttadk/kitex`
- `ttadk/overpass`
- `ttadk/backend-sdk`
- `ttadk/backend-test`
- `ttadk/common-test`
- `ttadk/gdpa`
- `ttadk/lark_cli`
- `ttadk/bits-unit-test-gen`
- `ttadk/tiktok-guidelines`

后续如果新增插件，统一按下面格式在 README 中补充：

- 声明插件包：`plugin-package-name`
- 展开插件：`plugin-a`、`plugin-b`、`plugin-c`
- 用途：一句话说明这组插件主要解决什么问题

这意味着项目后续可以优先从以下方向开始接入：

- 文档处理能力
- 外部知识 / 文档解析能力
- LangGraph 主图与路由骨架

## 建议的目录演进方向

当前仓库按顶层 `backend / frontend` 分离维护：

- `backend/`：Python + FastAPI + LangGraph 后端工程
- `frontend/`：当前 Web 控制台静态资源
- 当前 frontend 仍由 backend 提供静态文件服务，不是独立构建产物

```text
m1kasaz_agent/
├── backend/
│   ├── main.py
│   ├── pyproject.toml
│   ├── app/
│   │   ├── api/
│   │   ├── graph/
│   │   ├── nodes/
│   │   ├── subgraphs/
│   │   ├── tools/
│   │   ├── services/
│   │   ├── scheduler/
│   │   └── prompts/
│   └── tests/
├── frontend/
│   └── static/
├── data/
└── docs/
```

## 近期开发顺序建议

1. 搭建 LangGraph 主图，只做 `chat / document / paper` 三类意图路由
2. 先实现文档处理 MVP：`docx -> pdf`、`pdf/docx -> text`
3. 加入定时任务，支持每日论文推荐
4. 落地用户偏好与推荐历史存储
5. 再逐步扩展 API、通知和知识库能力

## 后续可以补充的内容

随着代码逐步落地，README 可以继续补充：

- 本地启动方式（默认进入 `backend/` 执行）
- 环境变量说明
- API / CLI 使用示例
- 测试方式（默认进入 `backend/` 执行）
- 项目目录说明
- Roadmap 与里程碑

## License

待补充。
