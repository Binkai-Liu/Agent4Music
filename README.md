<div align="center">

```text
    ___                    __  __ __  ___                     
   /   |  ____ ____  ____ / /_/ // / /   |  __  __ ____ (_)____
  / /| | / __ `/ _ \/ __ \ __/ // /_/ /| | / / / // __`/ // __/
 / ___ |/ /_/ /  __/ / / / /_/__  __/ /| |/ /_/ /\_, // // /__
/_/  |_|\__, /\___/_/ /_/\__/  /_/ /_/ |_|/____//___//_/ \___/ 
       /____/                                                   
```

**Agent4Music** — Intelligent Music Data Agent

An Agent System for Crawling, Analyzing & Visualizing Open Data of Modern Music Websites

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Vue](https://img.shields.io/badge/Vue-3.x-green.svg)](https://vuejs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## ⚠️ 合规声明（必读）

本项目**仅抓取各音乐平台公开、非版权、可访问的元数据**（公开榜单、热门歌单、公开艺人简介、歌词文本等）。

- **不**破解付费内容
- **不**爬取版权音频文件
- **不**恶意高频爬取
- 默认请求间隔 ≥ 1 秒，内置 URL 合规黑名单

请遵守目标站点服务条款与当地法律法规，仅供学习研究使用。

---

## 核心亮点

- **分层 Agent 架构**：LLM 决策 + 宿主执行 + 工具集 + Skill 按需加载
- **最新榜单**：QQ / 网易云 热歌、新歌、飙升、原创等多榜单一键实时拉取
- **喜好推荐**：拖拽曲风/场景标签与歌曲，智能匹配推荐歌单
- **多站点适配**：QQ 音乐、网易云音乐公开数据（配置化扩展）
- **Skills 系统**：数据清洗、歌词解析、曲风标签分类
- **子 Agent 并行**：多站点独立上下文并行采集
- **全功能 WebUI**：任务配置、实时监控、数据浏览、图表大屏、导出

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.10+, FastAPI, asyncio, SQLite |
| Agent | 自研四步握手 + 多模型 LLM Client |
| 爬虫 | httpx, Playwright |
| 前端 | Vue3, Vite, Element Plus, ECharts, TailwindCSS |
| 部署 | Docker, uvicorn |

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/YOUR_USERNAME/Agent4Music.git
cd Agent4Music
```

### 2. 安装依赖

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 配置 LLM（可选）

```bash
export OPENAI_API_KEY=your_key
# 或本地 Ollama：修改 config/llm_config.json provider 为 ollama
```

### 4. 一键启动

```bash
chmod +x start.sh
./start.sh
```

启动时将显示 ASCII Banner，并输出：

| 入口 | 地址 |
|------|------|
| **WebUI** | http://127.0.0.1:8120/ |
| **API 文档** | http://127.0.0.1:8120/docs |

### 5. WebUI 开发模式

```bash
# 终端 1
uvicorn api.main_api:app --host 0.0.0.0 --port 8120

# 终端 2
cd webui && npm install && npm run dev
# http://127.0.0.1:5173
```

### 6. Docker

```bash
docker compose up -d
```

## 示例脚本

```bash
python examples/skill_demo.py
python examples/single_site_demo.py qq
python examples/single_site_demo.py netease
python examples/batch_task_demo.py
```

## 已支持站点

| 站点 | ID | 支持类型 |
|------|-----|---------|
| QQ音乐 | `qq` | 热榜、歌单、歌手 |
| 网易云音乐 | `netease` | 热榜、歌单、歌手 |

## 项目结构

```
Agent4Music/
├── assets/banner.txt    # ASCII 启动 Banner
├── scripts/             # show_banner.sh
├── core/                # Agent 核心
├── tools/               # 原生工具集
├── skills/              # 按需加载技能
├── services/            # 站点适配 + 数据库
├── api/                 # FastAPI 接口
├── webui/               # Vue3 前端
├── config/              # 全局配置
└── examples/            # 入门示例
```

## 如何新增站点

1. 添加 `config/spider_rules/{site}.json`
2. 实现 `services/site_{site}.py` 继承 `BaseSiteAdapter`
3. 在 `services/factory.py` 注册

## 如何新增 Skill

1. 创建 `skills/{name}/SKILL.md`
2. 在 `skills/executor.py` 添加处理逻辑

## License

MIT — 详见 [LICENSE](LICENSE)
