# 🇩🇪 AI 智能体辅助大学德语个性化学习系统

<p align="center">
  <strong>SITP-German-AI-Agent</strong><br/>
  同济大学大学生创新训练项目 (SITP) · 校级项目
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-19.2-61DAFB?logo=react&logoColor=white" alt="React" />
  <img src="https://img.shields.io/badge/Vite-7.2-646CFF?logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Gemini_2.5_Flash-AI-4285F4?logo=google&logoColor=white" alt="Gemini" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker" />
</p>

---

## 📖 项目简介

在传统大学德语教学中，课堂练习时间有限、难以兼顾每位学生的个性化需求。本项目通过构建 **"教师 — 学生 — AI 智能体"** 三元协同教学模式，利用 Google Gemini 大语言模型作为德语 AI 助教，为学生提供 1 对 1 高频互动训练，为教师提供学情洞察与智能教学工具。

### 核心特性

| 模块           | 功能亮点                                                                                           |
| -------------- | -------------------------------------------------------------------------------------------------- |
| 🎓 **教师端**  | 教学仪表盘 · 学情监控 · AI 情景任务发布 · 智能试卷生成 · 作业 AI+人工双轨批改 · 个性化强化方案推送 |
| 📚 **学生端**  | AI 情景对话 · 词汇学习 · 语法练习 · 听说训练 · 写作辅助 · 错题本 · 学习进度追踪 · 收藏夹           |
| 🤖 **AI 引擎** | 基于 Gemini 2.5 Flash · 德语助教人设 · 语法纠错 · 中德双语解释                                     |

---

## 🏗️ 系统架构

```
                    ┌──────────────────────────────────────────┐
                    │          Docker Compose 容器编排           │
                    │                                          │
 用户浏览器 ──▶  ┌──┴────────────┐   ┌──────────────┐   ┌─────┴──────┐
    :80       │   Frontend    │   │   Backend    │   │ PostgreSQL │
              │   Nginx       │──▶│   FastAPI    │──▶│     16     │
              │   React SPA   │   │   Uvicorn    │   │   :5432    │
              └───────────────┘   └──────┬───────┘   └────────────┘
                                         │
                                  ┌──────▼───────┐
                                  │  Google AI   │
                                  │ Gemini 2.5   │
                                  │    Flash     │
                                  └──────────────┘
```

---

## 🛠️ 技术栈

### 前端 (Frontend)

| 技术                                                         | 版本  | 用途                   |
| ------------------------------------------------------------ | ----- | ---------------------- |
| [Vite](https://vitejs.dev/)                                  | 7.2   | 构建工具与开发服务器   |
| [React](https://react.dev/)                                  | 19.2  | UI 框架                |
| [React Router](https://reactrouter.com/)                     | 7.12  | 前端路由 (HashRouter)  |
| [Tailwind CSS](https://tailwindcss.com/)                     | 3.4   | 原子化 CSS 样式        |
| [Ant Design](https://ant.design/)                            | 6.2   | UI 组件库              |
| [Lucide React](https://lucide.dev/)                          | 0.562 | 矢量图标库             |
| [Axios](https://axios-http.com/)                             | 1.13  | HTTP 请求 (统一拦截器) |
| [React Markdown](https://github.com/remarkjs/react-markdown) | 10.1  | Markdown 渲染          |

### 后端 (Backend)

| 技术                                               | 用途              |
| -------------------------------------------------- | ----------------- |
| [FastAPI](https://fastapi.tiangolo.com/)           | Web 框架 (Python) |
| [Uvicorn](https://www.uvicorn.org/)                | ASGI 服务器       |
| [Google Generative AI SDK](https://ai.google.dev/) | Gemini 模型调用   |
| [SQLAlchemy](https://www.sqlalchemy.org/)          | ORM 数据库操作    |
| [Psycopg](https://www.psycopg.org/psycopg3/)       | PostgreSQL 驱动   |
| [Alembic](https://alembic.sqlalchemy.org/)         | 数据库迁移管理    |

### 基础设施 (DevOps)

| 技术                    | 用途                            |
| ----------------------- | ------------------------------- |
| Docker & Docker Compose | 容器化编排（三容器架构）        |
| Nginx                   | 前端静态资源托管 + API 反向代理 |
| PostgreSQL 16           | 关系型数据库（数据卷持久化）    |
| GitHub Actions          | CI/CD 自动化部署                |

---

## 📂 项目结构

```
SITP-German-AI-Agent/
├── frontend/                     # 前端项目
│   ├── src/
│   │   ├── api/
│   │   │   ├── config.js         # API 端点统一配置
│   │   │   └── request.js        # Axios 实例 (Token注入 + 401拦截)
│   │   ├── components/
│   │   │   └── Toast.jsx         # Toast 通知系统
│   │   ├── pages/
│   │   │   ├── teacher/          # 教师端页面
│   │   │   │   ├── TeacherLogin.jsx
│   │   │   │   ├── TeacherDashboard.jsx
│   │   │   │   ├── ScenarioLaunch.jsx
│   │   │   │   ├── ExamGenerator.jsx
│   │   │   │   └── StudentDetail.jsx
│   │   │   ├── student/          # 学生端页面
│   │   │   └── Login.jsx         # 全局入口登录页
│   │   ├── App.jsx               # 路由配置 (HashRouter)
│   │   └── main.jsx              # 应用入口
│   ├── nginx.conf                # 生产环境 Nginx 配置
│   ├── Dockerfile                # 前端容器构建
│   ├── vite.config.js            # Vite 配置 (含开发代理)
│   └── package.json
│
├── backend/                      # 后端项目
│   ├── main.py                   # API 端点入口 (FastAPI)
│   ├── crud/                     # 数据库 CRUD 操作层
│   ├── models/                   # SQLAlchemy ORM 模型
│   ├── schemas/                  # Pydantic 数据校验模型
│   ├── db/
│   │   ├── session.py            # 数据库会话管理
│   │   └── sql/                  # SQL 初始化脚本
│   │       ├── 001_init_schema.sql
│   │       └── 002_seed_demo.sql
│   ├── Dockerfile                # 后端容器构建
│   └── requirements.txt          # Python 依赖
│
├── doc/                          # 项目文档
│   └── User_Manuals/             # 用户操作手册
│
├── docker-compose.yml            # 容器编排 (一键启动)
├── .env                          # 环境变量 (需手动创建)
├── .github/workflows/            # GitHub Actions CI/CD
└── README.md
```

---

## ⚠️ 网络代理配置（国内环境必需）

本项目的 AI 功能依赖 Google Gemini API，其服务器在国内无法直连。**因为在国内开发，必须配置科学上网代理，否则所有 AI 相关功能将无法使用**（前端页面和数据库功能不受影响）。

**配置方法**：在 `.env` 文件中添加以下两行，将端口号改为你本机代理工具实际使用的端口：

```dotenv
HTTP_PROXY=http://127.0.0.1:你的代理端口
HTTPS_PROXY=http://127.0.0.1:你的代理端口
```

常见代理工具的默认端口参考：

| 代理工具                        | 默认 HTTP 端口          |
| ------------------------------- | ----------------------- |
| Clash for Windows / Clash Verge | `7890` 或你实际的端口号 |
| v2rayN                          | `10809`                 |

> 💡 如何确认端口？打开你的代理客户端，在设置中查看 **HTTP 代理端口**（不是 SOCKS 端口）。
>
> 如果你在海外或不需要代理，不写这两行即可，后端代码已做兼容处理，不会报错。

---

## 🚀 快速开始

### 方式一：Docker Compose 一键部署 (推荐)

> 无需本地安装 Node.js 或 Python，只需 [Docker Desktop](https://www.docker.com/products/docker-desktop/)。

**1. 配置环境变量**

```bash
# 在项目根目录创建 .env 文件
echo "GOOGLdsdE_API_KEY=你的_Google_Gemini_API_密钥" > .env
```

> 💡 Gemini API Key 获取方式：访问 [Google AI Studio](https://aistudio.google.com/apikey) 申请免费密钥。

**2. 构建并启动**

```bash
docker compose up -d --build
```

**3. 访问系统**

| 服务             | 地址                             |
| ---------------- | -------------------------------- |
| 🌐 前端首页      | http://localhost                 |
| 🎓 教师端登录    | http://localhost/#/teacher/login |
| 📚 学生端登录    | http://localhost/#/student/login |
| 📡 后端 API 文档 | http://localhost:8000/docs       |
| 🔍 后端健康检查  | http://localhost:8000/           |

**常用运维命令**

```bash
# 查看所有容器状态
docker compose ps

# 查看实时日志
docker compose logs -f

# 仅查看后端日志
docker compose logs -f backend

# 停止所有容器
docker compose down

# 停止并清除数据库数据 (慎用)
docker compose down -v
```

---

### 方式二：本地开发环境

适用于需要修改代码并实时预览的开发场景。

> **前置要求**：Node.js ≥ 18、Python ≥ 3.10、正在运行的 PostgreSQL 16 实例

**1. 启动数据库**

可使用 Docker 单独启动 PostgreSQL：

```bash
docker compose up -d db
```

**2. 启动后端**

```bash
cd backend

# 创建并激活虚拟环境
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # macOS/Linux

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
$env:GOOGLE_API_KEY="你的密钥"          # PowerShell
# export GOOGLE_API_KEY="你的密钥"      # macOS/Linux

# 启动开发服务器 (热重载)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**3. 启动前端**

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

> 前端开发服务器运行在 `http://localhost:5173`，已配置 Vite Proxy 将 `/api` 请求自动代理至后端 `http://localhost:8000`，无需手动修改 API 地址。

---

## 📡 API 概览

| 方法   | 端点                       | 功能                 |
| ------ | -------------------------- | -------------------- |
| `POST` | `/api/chat`                | AI 德语对话 (学生端) |
| `POST` | `/api/auth/login`          | 用户登录认证         |
| `GET`  | `/api/teacher/dashboard`   | 教学仪表盘数据       |
| `POST` | `/api/scenario/publish`    | 发布情景任务         |
| `POST` | `/api/exam/generate`       | 生成智能试卷         |
| `GET`  | `/api/student/detail`      | 学生详细画像         |
| `GET`  | `/api/homework/detail`     | 作业文件详情         |
| `POST` | `/api/homework/save`       | 保存教师评分         |
| `POST` | `/api/student/push-scheme` | 推送个性化强化方案   |

> 完整 API 文档（自动生成）：启动后端后访问 http://localhost:8000/docs

---

## 📚 用户手册

详细的操作指南请参考 [`doc/User_Manuals/`](doc/User_Manuals/) 目录：

- [教师端后台操作手册](doc/User_Manuals/教师端后台手册.md) — 涵盖登录、仪表盘、情景发布、试卷生成、学生管理全流程

---

## 👥 项目团队

| 角色           | 姓名   | 学院                 | 分工                           |
| -------------- | ------ | -------------------- | ------------------------------ |
| **指导教师**   | 汤春艳 | 外国语学院           | 教学理论指导、资源支持         |
| **项目负责人** | 魏世杰 | 计算机科学与技术学院 | 系统架构设计、服务器部署与维护 |
| **核心成员**   | 洪超慧 | 中德工程学院         | 前端界面 — 学生端              |
| **核心成员**   | 童文景 | 计算机科学与技术学院 | 前端界面 — 教师端              |
| **核心成员**   | 周雨晗 | 外国语学院           | 德语语料搜集、数据库输入       |
| **核心成员**   | 王莹   | 计算机科学与技术学院 | AI 智能体搭建                  |

---

## 📄 许可证

本项目为同济大学 SITP 校级科研项目，仅供学术研究与教学使用。
