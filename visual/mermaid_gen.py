"""Auto-generate Mermaid architecture diagrams."""

from __future__ import annotations

ARCHITECTURE_DIAGRAM = """flowchart TB
    WebUI[Vue3 WebUI] --> FastAPI
    FastAPI --> AgentLoop
    AgentLoop --> LLM[LLM Client]
    AgentLoop --> Tools[Tools Layer]
    AgentLoop --> Skills[Skills Layer]
    AgentLoop --> SubAgent[Sub Agents]
    SubAgent --> QQ[QQ Music]
    SubAgent --> NetEase[NetEase Music]
    Tools --> HTTP[http_request]
    Tools --> Browser[playwright]
    FastAPI --> WS[WebSocket Logs]
"""

BUSINESS_FLOW = """flowchart LR
    A[用户提交任务] --> B[Agent分析站点]
    B --> C{单/多站点}
    C -->|单站点| D[主Agent爬取]
    C -->|多站点| E[子Agent并行]
    D --> F[原始数据]
    E --> F
    F --> G{需要处理?}
    G -->|是| H[Skill清洗/分类]
    G -->|否| I[入库]
    H --> I
    I --> J[WebUI展示]
"""


def get_architecture_diagram() -> str:
    return ARCHITECTURE_DIAGRAM


def get_business_flow() -> str:
    return BUSINESS_FLOW
