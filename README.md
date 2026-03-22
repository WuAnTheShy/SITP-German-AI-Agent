# 🇩🇪 AI 智能体辅助大学德语个性化学习系统

<p align="center">
  <strong>SITP-German-AI-Agent</strong><br/>
  同济大学大学生创新训练项目 (SITP) · 校级项目
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-19.2-61DAFB?logo=react&logoColor=white" alt="React" />
  <img src="https://img.shields.io/badge/Vite-7.2-646CFF?logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Qwen-Plus_AI-FF6B6B?style=flat-square" alt="Qwen" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker" />
</p>

---

## 📖 项目简介

在传统大学德语教学中，课堂练习时间有限、难以兼顾每位学生的个性化需求。本项目通过构建 **"教师 — 学生 — AI 智能体"** 三元协同教学模式，支持 Qwen（通义千问）与 LM Studio（本地）双模式大语言模型接入，为学生提供 1 对 1 高频互动训练，为教师提供学情洞察与智能教学工具。

### 核心特性

| 模块           | 功能亮点                                                                                           |
| -------------- | -------------------------------------------------------------------------------------------------- |
| 🛡️ **管理员端** | 教师审核与账号启停 · 班级创建/编辑/删除 · 学生名单与分班管理 · 账号密码重置（教师/学生） · 系统审核策略开关 |
| 🎓 **教师端**  | 教学仪表盘 · 学情监控 · AI教研助手 · 智能试卷生成 · 情景任务发布 · 发布历史溯源 · 作业全轨批改      |
| 📚 **学生端**  | 专属 AI 语伴 · 词汇/语法/听说写作跨板块评测 · 错题精练诊断 · 学习进度追踪 · 收藏夹          |
| 🤖 **AI 引擎** | Qwen / LM Studio 双模式 · 德语助教人设 · 语法纠错 · 中德双语解释                                     |

---

## 🏗️ 系统架构

```
                    ┌──────────────────────────────────────────┐
                    │          Docker Compose 容器编排          │
                    │                                          │
 用户浏览器 ──▶┌────┴──────────┐    ┌──────────────┐    ┌───────┴────┐
    :80        │   Frontend    │    │   Backend    │    │ PostgreSQL │
               │   Nginx       │──▶│   FastAPI    │──▶│     16     │
               │   React SPA   │    │   Uvicorn    │    │   :5432    │
               └───────────────┘    └──────┬───────┘    └────────────┘
                                           │
                                    ┌──────▼──────────────┐
                                    │ OpenAI Compatible LLM│
                                    │ Qwen / LM Studio     │
                                    └──────────────────────┘
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
| [Qwen API](https://help.aliyun.com/zh/dashscope/) / [LM Studio](https://lmstudio.ai/) | OpenAI 兼容模型调用（云端/本地） |
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
├── backend/                      # 后端项目
│   ├── core/                    # 核心功能模块
│   │   ├── deps.py              # 依赖注入
│   │   ├── password.py          # 密码处理
│   │   └── responses.py         # 统一响应格式
│   ├── crud/                    # 数据库 CRUD 操作层
│   │   └── repositories.py      # 数据仓库实现
│   ├── db/                      # 数据库相关
│   │   ├── sql/                 # SQL 初始化脚本
│   │   ├── session.py           # 数据库会话管理
│   │   └── init_db.py           # 数据库初始化
│   ├── models/                  # SQLAlchemy ORM 模型
│   │   └── entities.py          # 数据库实体定义
│   ├── routers/                 # API 路由
│   │   ├── admin.py             # 管理员端接口
│   │   ├── chat.py              # AI 对话接口
│   │   ├── student.py           # 学生基础接口
│   │   ├── student_learning.py  # 学生学习模块接口
│   │   ├── student_tasks.py     # 学生任务/考试接口
│   │   ├── teacher.py           # 教师相关接口
│   │   └── auth.py              # 认证接口
│   ├── schemas/                 # Pydantic 数据校验模型
│   │   └── entities.py          # 数据传输对象
│   ├── services/                # 业务逻辑服务
│   │   ├── llm.py               # 大语言模型服务
│   │   └── session.py           # 会话管理服务
│   ├── main.py                  # API 端点入口 (FastAPI)
│   ├── Dockerfile               # 后端容器构建
│   └── requirements.txt         # Python 依赖
│
├── frontend/                    # 前端项目
│   ├── src/
│   │   ├── api/                 # API 调用
│   │   │   ├── config.js        # API 端点统一配置
│   │   │   └── request.js       # Axios 实例
│   │   ├── components/          # 通用组件
│   │   │   ├── Toast.jsx        # Toast 通知系统
│   │   │   └── ProtectedRoute.jsx # 路由保护
│   │   ├── context/             # 全局上下文
│   │   │   └── ThemeContext.jsx # 主题管理
│   │   ├── pages/               # 页面组件
│   │   │   ├── student/         # 学生端页面
│   │   │   │   ├── AISceneChat.jsx # AI 场景对话
│   │   │   │   ├── VocabLearning.jsx # 词汇学习
│   │   │   │   └── GrammarPractice.jsx # 语法练习
│   │   │   ├── teacher/         # 教师端页面
│   │   │   │   ├── TeacherDashboard.jsx # 教师仪表盘
│   │   │   │   ├── ScenarioLaunch.jsx # 情景任务发布
│   │   │   │   └── ExamGenerator.jsx # 智能试卷生成
│   │   │   └── Login.jsx        # 全局入口登录页
│   │   ├── App.jsx              # 路由配置
│   │   └── main.jsx             # 应用入口
│   ├── .env.development         # 开发环境变量
│   ├── .env.production          # 生产环境变量
│   ├── nginx.conf               # 生产环境 Nginx 配置
│   ├── Dockerfile               # 前端容器构建
│   └── package.json             # 前端依赖
│
├── doc/                         # 项目文档
│   ├── Database/                # 数据库相关文档
│   ├── Maintenance/             # 运维相关文档
│   ├── Technical/               # 技术相关文档
│   └── User_Manuals/            # 用户操作手册
│
├── docker-compose.yml           # 容器编排 (一键启动)
├── .env                         # 环境变量 (需手动创建，含 API Key)
├── .gitignore                   # Git 忽略文件配置
└── README.md                    # 项目说明文档
```

---

## 🚀 快速开始

### 前置准备：LLM 模式与环境变量

本项目后端支持两种 LLM provider：

- `qwen`：调用阿里云 DashScope（在线）
- `lmstudio`：调用本机 LM Studio OpenAI 兼容服务（本地）

在项目根目录创建 `.env` 文件，并按需二选一配置。

**方案 A：Qwen（在线）**

```dotenv
LLM_PROVIDER=qwen
QWEN_API_KEY=你的_通义千问_API_密钥
# 可选，不填则使用后端默认值
# QWEN_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
# 可选，不填则使用默认模型 qwen3.5-plus
# LLM_MODEL=qwen3.5-plus
```

> 💡 Qwen API Key 获取方式：访问 [阿里云 DashScope](https://dashscope.aliyun.com/) 申请 API 密钥。

**方案 B：LM Studio（本地）**

```dotenv
LLM_PROVIDER=lmstudio

# 使用 docker compose 启动后端容器时
LMSTUDIO_BASE_URL=http://host.docker.internal:1234

# 本地运行后端时使用，请改为
# LMSTUDIO_BASE_URL=http://127.0.0.1:1234

# 模型名需与 LM Studio 当前加载模型一致
LMSTUDIO_MODEL=qwen2.5-7b-instruct

# LM Studio 默认可留空；如你在 LM Studio 开启了鉴权再填写
LMSTUDIO_API_KEY=
```

---

### 方式一：Docker Compose 一键部署（推荐）

> 无需本地安装 Node.js 或 Python，只需 [Docker Desktop](https://www.docker.com/products/docker-desktop/)。

```bash
docker compose up -d --build
```

> 💡 Docker 模式下，前端 Nginx 会自动将 `/api` 请求反向代理到后端容器，无需任何额外配置。无论是本地 Docker 还是服务器 Docker，前端代码完全一致。

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

# 推荐直接在项目根目录维护 .env 文件；临时调试也可在当前终端导出变量
# PowerShell 示例（LM Studio 本地模式）：
# $env:LLM_PROVIDER="lmstudio"
# $env:LMSTUDIO_BASE_URL="http://127.0.0.1:1234"
# $env:LMSTUDIO_MODEL="qwen2.5-7b-instruct"

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

## 🧠 LM Studio 本地使用说明（重点）

### 1. 安装并准备模型

1. 安装 [LM Studio](https://lmstudio.ai/)（Windows/macOS/Linux）。
2. 在 LM Studio 内下载可用的对话模型（建议 7B 级别先跑通流程）。
3. 确认模型已加载，并可在 Chat 页面正常响应。

### 2. 启动 LM Studio 本地 OpenAI 服务

在 LM Studio 的开发者/服务页面启动本地 API 服务，默认监听：

- `http://127.0.0.1:1234`

本项目后端会请求：

- `/v1/chat/completions`

### 3. 配置项目 `.env`

#### 本地开发（后端直接在宿主机运行）

```dotenv
LLM_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://127.0.0.1:1234
LMSTUDIO_MODEL=qwen2.5-7b-instruct
LMSTUDIO_API_KEY=
```

#### Docker Compose（后端在容器内运行）

```dotenv
LLM_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://host.docker.internal:1234
LMSTUDIO_MODEL=qwen2.5-7b-instruct
LMSTUDIO_API_KEY=
```

> 关键点：容器内 `127.0.0.1` 指向容器自身，不是宿主机，因此 Docker 模式应使用 `host.docker.internal` 访问宿主机上的 LM Studio。

### 4. 启动系统并验证

启动后端（本地）或全栈（Docker）后，查看后端日志应出现类似信息：

- `[API] LLM_PROVIDER=lmstudio, MODEL_ID=...`
- `[API] API_URL=http://.../v1/chat/completions`
- `[API] LM Studio 模式启用（可离线运行）`

若页面可正常发起 AI 对话并返回结果，说明联通成功。

### 5. 常见问题排查

| 现象 | 常见原因 | 处理方式 |
| ---- | ---- | ---- |
| AI 对话无响应 / 超时 | LM Studio 服务未启动 | 在 LM Studio 中重新启动本地 API 服务 |
| 后端报 404 | `LMSTUDIO_BASE_URL` 配错（缺端口或路径） | 使用 `http://127.0.0.1:1234` 或 `http://host.docker.internal:1234`，不要手动拼 `/v1/chat/completions` |
| Docker 模式连接失败 | 容器内写成了 `127.0.0.1` | 改为 `host.docker.internal` |
| 模型调用报错 | `LMSTUDIO_MODEL` 与当前加载模型名不一致 | 在 LM Studio 中复制准确模型 ID 到 `.env` |
| 切换 provider 后行为异常 | 后端未重启，仍使用旧环境变量 | 重启后端服务（本地重启 uvicorn / Docker 重启 backend） |

---

### 演示账号

系统首次启动时会自动初始化以下演示账号，可直接用于登录测试（含多班级样例）：

| 角色  | 用户名/学号 | 密码 | 班级 | 备注 |
| ----  | ----------- | ---- | ---- | ---- |
| 教师  | `t_zhang` | `demo_hash_teacher` | 软件工程(四)班（SE-2026-4） | 张老师 |
| 教师  | `t_liu` | `demo_hash_teacher` | 数据科学(一)班（DS-2026-1） | 刘老师 |
| 教师  | `t_chen` | `demo_hash_teacher` | 德语强化(二)班（FA-2025-2） | 陈老师 |
| 学生  | `2452001` | `demo_hash_student` | 软件工程(四)班（SE-2026-4） | 李娜（含完整演示数据） |
| 学生  | `2452002` | `demo_hash_student` | 软件工程(四)班（SE-2026-4） | 王强 |
| 学生  | `2452003` | `demo_hash_student` | 数据科学(一)班（DS-2026-1） | 赵敏 |
| 学生  | `2452004` | `demo_hash_student` | 数据科学(一)班（DS-2026-1） | 孙浩 |
| 学生  | `2452005` | `demo_hash_student` | 德语强化(二)班（FA-2025-2） | 钱雨 |
| 学生  | `2452006` | `demo_hash_student` | 德语强化(二)班（FA-2025-2） | 何宁 |
| 管理员  | `admin` | `admin123` | - | 管理员 |

> ⚠️ 教师端和学生端均已启用密码校验与权限隔离，学生账号无法访问教师端功能，反之亦然。

### 密码与认证说明

- 前端传输：登录与改密请求对密码执行 `SHA-256` 后再传输。
- 后端存储：统一存储为 `bcrypt(sha256(password))`，并兼容历史旧数据自动迁移。
- 管理员能力：管理员可在管理端重置教师/学生账号密码。

---

## 🆕 近期功能完善

- 管理员端教师管理：支持教师搜索、审核状态调整、登录权限启停与删除。
- 管理员端班级管理：支持新建班级、编辑班级、删除班级、复制邀请码。
- 管理员端学生管理：支持学生搜索筛选、状态维护、分班调整、活跃度与综合分维护、删除。
- 管理员端账号安全：支持为教师与学生账号重置密码。
- 系统设置：支持教师注册审核、学生注册审核开关。

---

## 🔄 环境模式切换

前端通过 Vite 环境变量实现三种运行模式的**零改动切换**：

| 运行模式 | 启动方式 | 前端访问地址 | API 请求路由 |
| --------- | -------------------------------- | -------------------- | ---------------------------------------- |
| 🖥️ 本地开发 | `npm run dev` | `localhost:5173` | Vite Proxy → `localhost:8000` |
| 🐳 本地 Docker | `docker compose up -d --build` | `localhost:80` | Nginx 反向代理 → `backend:8000` |
| 🌐 服务器 Docker | 同上 (在服务器执行) | `服务器IP:80` | Nginx 反向代理 → `backend:8000` |

**配置文件说明**

| 文件 | 用途 | 是否提交到 Git |
| ------ | ------ | ------------- |
| `frontend/.env.development` | 开发模式默认配置（Proxy 目标地址等） | ✅ 是 |
| `frontend/.env.production` | 生产模式默认配置 | ✅ 是 |
| `frontend/.env.development.local` | **本地覆盖**（如需代理到远程服务器） | ❌ 否 |

**进阶用法：本地开发时代理到远程服务器**

如果需要在本地开发（`npm run dev`）时直接代理到远程服务器的后端，创建 `frontend/.env.development.local`：

```dotenv
# 将代理目标指向远程服务器 (该文件已被 .gitignore 忽略)
VITE_DEV_PROXY_TARGET=http://49.234.185.167:9000
```

> `.local` 文件优先级高于同名非 `.local` 文件，且不会被提交到 Git。

---

## 🔧 运维参考

### Docker 常用命令

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

# 清理所有未使用的数据、镜像、容器和卷 (无提示)
docker system prune -a --volumes -f

# 清理未使用的悬空镜像和停止的容器
docker system prune

# 查看 Docker 磁盘使用情况
docker system df
```

---

## 📡 API 概览

| 方法   | 端点                       | 功能                 |
| ------ | -------------------------- | -------------------- |
| `POST` | `/api/auth/login` | 教师/管理员登录 |
| `POST` | `/api/auth/student-login` | 学生登录 |
| `PUT` | `/api/user/password` | 教师/学生自助修改密码 |
| `GET` | `/api/admin/teachers` | 管理员查看教师列表 |
| `PUT` | `/api/admin/teachers/{user_id}` | 管理员更新教师状态与启停 |
| `DELETE` | `/api/admin/teachers/{user_id}` | 管理员删除教师账号 |
| `GET` | `/api/admin/students` | 管理员查看学生列表 |
| `PUT` | `/api/admin/students/{student_id}` | 管理员更新学生信息 |
| `DELETE` | `/api/admin/students/{student_id}` | 管理员删除学生账号 |
| `PUT` | `/api/admin/users/{user_id}/password` | 管理员重置教师/学生密码 |
| `GET` | `/api/admin/classes` | 管理员查看班级列表 |
| `POST` | `/api/admin/classes` | 管理员创建班级 |
| `PUT` | `/api/admin/classes/{class_id}` | 管理员编辑班级 |
| `DELETE` | `/api/admin/classes/{class_id}` | 管理员删除班级 |
| `PUT` | `/api/admin/system/settings` | 管理员更新审核策略 |
| `GET`  | `/api/teacher/dashboard` | 教师教学仪表盘 |
| `GET`  | `/api/teacher/students` | 教师查看班内学生 |
| `POST` | `/api/scenario/publish` | 教师发布情景任务 |
| `POST` | `/api/exam/generate` | 教师生成智能试卷 |
| `GET` | `/api/student/favorites/list` | 学生查看收藏列表 |
| `DELETE` | `/api/student/favorites/{fav_id}` | 学生删除收藏 |
| `GET` | `/api/student/learning/progress` | 学生学习进度总览 |

> 完整 API 文档（自动生成）：启动后端后访问 http://localhost:8000/docs

---

## 📚 项目文档 (Documentation)

详细的系统设计与操作指南请参考 [`doc/`](doc/) 目录：

### 👤 用户手册 (User Manuals)
- [教师端后台操作手册](doc/User_Manuals/教师端后台手册.md) — 涵盖登录、仪表盘、情景发布、试卷生成、作业批改等全流程。
- [学生端应用手册](doc/User_Manuals/学生端应用手册.md) — 介绍任务中心、AI 语伴对话、考试系统及专项学习工具。

### 🔧 技术文档 (Technical Docs)
- [系统流程与架构](doc/Technical/系统流程与架构.md) — 核心业务流程图（Mermaid）与数据流转说明。
- [数据库架构说明](doc/Database/数据库开发使用说明.md) — 详述 27 张核心数据表的结构与关联。
- [API 接口参考手册](doc/Technical/API参考手册.md) — 各端点功能、请求方法及响应格式列表。
- [AI 智能体集成说明](doc/Technical/AI智能体集成说明.md) — 深入讲解提示词工程、Qwen 集成与结构化输出处理。
- [开发维护与扩展导引](doc/Technical/开发维护与扩展导引.md) — 代码结构解析与扩展开发指南。

### 🚀 运维指南 (Maintenance)
- [环境部署与维护指南](doc/Maintenance/环境部署与维护指南.md) — Docker 部署、数据备份、代理配置及安全建议。

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
