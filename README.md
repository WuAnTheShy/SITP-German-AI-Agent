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

| 模块            | 功能亮点                                                                                                    |
| --------------- | ----------------------------------------------------------------------------------------------------------- |
| 🛡️ **管理员端** | 教师审核与账号启停 · 班级创建/编辑/删除 · 学生名单与分班管理 · 账号密码重置（教师/学生） · 系统审核策略开关 |
| 🎓 **教师端**   | 教学仪表盘 · 学情监控 · AI教研助手 · 智能试卷生成 · 情景任务发布 · 发布历史溯源 · 作业全轨批改              |
| 📚 **学生端**   | 专属 AI 语伴 · 词汇/语法/听说写作跨板块评测 · 错题精练诊断 · 学习进度追踪 · 收藏夹                          |
| 🤖 **AI 引擎**  | Qwen / LM Studio 双模式 · 德语助教人设 · 语法纠错 · 中德双语解释                                            |

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

| 技术                                                                                  | 用途                             |
| ------------------------------------------------------------------------------------- | -------------------------------- |
| [FastAPI](https://fastapi.tiangolo.com/)                                              | Web 框架 (Python)                |
| [Uvicorn](https://www.uvicorn.org/)                                                   | ASGI 服务器                      |
| [Qwen API](https://help.aliyun.com/zh/dashscope/) / [LM Studio](https://lmstudio.ai/) | OpenAI 兼容模型调用（云端/本地） |
| [SQLAlchemy](https://www.sqlalchemy.org/)                                             | ORM 数据库操作                   |
| [Psycopg](https://www.psycopg.org/psycopg3/)                                          | PostgreSQL 驱动                  |
| [Alembic](https://alembic.sqlalchemy.org/)                                            | 数据库迁移管理                   |

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
│   │   ├── sql/                 # 历史基线脚本（由 Alembic 基线迁移引用）
│   │   ├── session.py           # 数据库会话管理
│   │   └── init_db.py           # 历史工具（当前不作为主流程）
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

## 🚀 部署与运维

### 📋 前置准备：环境变量配置

系统核心配置均通过 `.env` 文件驱动，**需手动在项目根目录创建或编辑**（`.env.example` 仅供参考）。

#### 核心配置项速查

| 变量名                            | 类型   | 必填   | 生产建议值                                 | 说明                                       |
| --------------------------------- | ------ | ------ | ------------------------------------------ | ------------------------------------------ |
| `APP_ENV`                         | 字符串 | ✅     | `production`                               | 运行环境标志                               |
| `POSTGRES_USER`                   | 字符串 | ✅     | `postgres`                                 | 数据库用户名（通常不变）                   |
| `POSTGRES_PASSWORD`               | 字符串 | ✅     | 高强度密码                                 | 数据库密码，Docker Compose 必填            |
| `POSTGRES_DB`                     | 字符串 | ✅     | `sitp_german_ai_agent`                     | 数据库名                                   |
| `INIT_ADMIN_USERNAME`             | 字符串 | ✅     | `admin`                                    | 首次启动创建的管理员用户名                 |
| `INIT_ADMIN_PASSWORD`             | 字符串 | ✅     | 高强度密码                                 | 首次启动创建的管理员密码                   |
| `AUTH_TOKEN_SECRET`               | 字符串 | ✅     | 32+ 随机字符                               | 令牌签名密钥，**绝不能硬编码在代码中**     |
| `RESET_ADMIN_PASSWORD_ON_STARTUP` | 布尔   | ⭕     | `false`                                    | 每次启动是否重置管理员密码（生产 false）   |
| `RESET_DEMO_PASSWORDS_ON_STARTUP` | 布尔   | ⭕     | `false`                                    | 每次启动是否重置演示账号密码（生产 false） |
| `ENABLE_DEMO_SEED`                | 布尔   | ⭕     | `false`                                    | 是否初始化演示数据（生产 false）           |
| `DEMO_TEACHER_PASSWORD`           | 字符串 | ⭕     | 高强度密码                                 | 演示教师账号密码（可留空让系统随机生成）   |
| `DEMO_STUDENT_PASSWORD`           | 字符串 | ⭕     | 高强度密码                                 | 演示学生账号密码（可留空让系统随机生成）   |
| `CORS_ALLOW_ORIGINS`              | 字符串 | ⭕     | 生产域名                                   | 前端域名（同域留空，跨域用逗号分隔）       |
| `LLM_PROVIDER`                    | 字符串 | ✅     | `qwen` 或 `lmstudio`                       | 大语言模型提供商                           |
| `QWEN_API_KEY`                    | 字符串 | 有条件 | 阿里云密钥                                 | 使用 Qwen 时必填                           |
| `LMSTUDIO_BASE_URL`               | 字符串 | 有条件 | Docker: `http://host.docker.internal:1234` | 使用 LM Studio 时必填                      |
| `LMSTUDIO_MODEL`                  | 字符串 | 有条件 | `qwen2.5-7b-instruct`                      | LM Studio 模型 ID（需与实际加载模型一致）  |
| `DEBUG_LLM_LOGS`                  | 布尔   | ⭕     | `false`                                    | 是否打印 LLM 调试日志（生产 false）        |

#### 完整配置示例（生产推荐）

```dotenv
# ===== 运行环境 =====
APP_ENV=production

# ===== 数据库配置（Docker Compose 必填）=====
POSTGRES_USER=postgres
POSTGRES_PASSWORD=ChangeThisDbPass_2026_SITP!
POSTGRES_DB=sitp_german_ai_agent

# ===== 初始管理员账号 =====
INIT_ADMIN_USERNAME=admin
INIT_ADMIN_PASSWORD=admin123

# ===== 令牌与鉴权 =====
AUTH_TOKEN_SECRET=SITP_German_Agent_Token_Secret_2026_Replace_Me_32Plus
AUTH_TOKEN_TTL_HOURS=12
ALLOW_LEGACY_TOKENS=false

# ===== 账号初始化策略 =====
ENABLE_DEMO_SEED=false
RESET_ADMIN_PASSWORD_ON_STARTUP=false
RESET_DEMO_PASSWORDS_ON_STARTUP=false
DEMO_TEACHER_PASSWORD=TeacherDemo@2026!
DEMO_STUDENT_PASSWORD=StudentDemo@2026!

# ===== CORS 与调试 =====
CORS_ALLOW_ORIGINS=https://your-domain.com
DEBUG_LLM_LOGS=false

# ===== 大语言模型（二选一）=====
LLM_PROVIDER=qwen
QWEN_API_KEY=sk-your-actual-qwen-api-key
# QWEN_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
# LLM_MODEL=qwen3.5-plus

# 如使用 LM Studio 则改为：
# LLM_PROVIDER=lmstudio
# LMSTUDIO_BASE_URL=http://host.docker.internal:1234
# LMSTUDIO_MODEL=qwen2.5-7b-instruct
```

#### LLM 配置选择

**方案A：Qwen 在线模式（推荐生产环境）**

- 无需本地部署模型，依赖阿里云服务
- 申请 API Key：https://dashscope.aliyun.com/
- 配置 `.env`：

```dotenv
LLM_PROVIDER=qwen
QWEN_API_KEY=sk-your-dashscope-api-key
# 可选参数，不填则使用后端默认值
# QWEN_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
# LLM_MODEL=qwen3.5-plus
```

**方案B：LM Studio 本地模式（推荐开发/离线场景）**

- 模型本地部署，完全离线可用
- 模型选择：推荐 Qwen 2.5 7B 模板开始测试
- 启动 LM Studio API 服务（默认 `http://127.0.0.1:1234`）
- 配置 `.env`（需分情况）：

| 运行场景                     | 配置值                                               |
| ---------------------------- | ---------------------------------------------------- |
| 后端在宿主机运行（本地开发） | `LMSTUDIO_BASE_URL=http://127.0.0.1:1234`            |
| 后端在 Docker 容器运行       | `LMSTUDIO_BASE_URL=http://host.docker.internal:1234` |

---

### 🐳 Docker Compose 完整部署流程（推荐）

本部分详细讲解 Docker Compose 一键部署的完整流程、工作原理、常见问题和解决方案。

#### 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose 网络 (bridge)              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐      ┌──────────────────────┐    │
│  │    Nginx 容器        │      │   Backend 容器       │    │
│  │    (前端静态+反代)   │◄────►│   (FastAPI Uvicorn)  │    │
│  │    :80               │      │    :8000             │    │
│  └──────────────────────┘      └──────────▲───────────┘    │
│           ▲                                 │                 │
│           │                                 │                 │
│     (用户浏览器)                       ┌─────▼──────────┐   │
│           │                           │ PostgreSQL 容器 │   │
│           │                           │    :5432       │   │
│           │                           │    (数据库)    │   │
│           │                           └────────────────┘   │
│           │                                                  │
│  (外界无法直接访问 Backend/DB，必须通过 Nginx)             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**关键点：**

1. **Nginx 角色**：前端静态资源托管 + API 请求反向代理到后端
2. **容器隔离**：后端和数据库不直接暴露给外界，通过 Nginx 转发业务请求
3. **网络通信**：容器间通过容器名作为主机名进行通信（如 `backend:8000`）
4. **宿主机访问**：`http://localhost/` 或 `http://服务器IP/` 访问 Nginx，后者再代理到内部容器

#### 第 1 步：准备 `.env` 文件

在项目根目录创建或编辑 `.env`，并使用上节"完整配置示例"的内容。**关键约束：**

- `POSTGRES_PASSWORD` 不能为空或纯数字（PostgreSQL 的严格要求）
- `AUTH_TOKEN_SECRET` 建议 32+ 随机字符
- 敏感信息（密钥、密码）不要提交到 Git

**验证方式：**确保根目录可见 `.env` 文件：

```bash
# Windows PowerShell
Get-Item .env -Force  # 应显示文件

# Linux/macOS
ls -la .env           # 应显示文件
```

#### 场景 A：首次部署（无历史数据卷）

适用条件：

- 第一次在这台机器部署
- 或执行过 `docker compose down -v`（数据库卷已清空）

执行步骤：

```bash
# 1) 构建镜像并后台启动
docker compose up -d --build

# 2) 检查容器状态（应看到 frontend/backend/db 均为 Up）
docker compose ps

# 3) 查看后端启动日志
docker compose logs -f backend
```

成功判定：

- 后端日志出现 `Application startup complete`
- 打开 `http://localhost`（或 `http://服务器IP`）能看到登录页

首次部署后建议立即执行健康检查：

```bash
# 后端健康检查（预期 200）
curl -i http://localhost:9000/

# 反向代理链路检查（预期 401，不应是 502）
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"wrong_password"}'

# 使用当前 .env 示例管理员口令验证登录（预期 code=0）
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

#### 场景 B：升级部署（已有历史数据卷）

适用条件：

- 机器上已存在历史数据库卷（如 `pg_data`）
- 你修改了 `.env`、镜像版本或业务代码并重新部署

执行步骤：

```bash
# 1) 拉起新版本容器
docker compose up -d --build

# 2) 查看状态与日志
docker compose ps
docker compose logs -f backend
```

升级部署最容易踩坑的是数据库密码不同步。

原因说明：PostgreSQL 仅在首次初始化时读取 `.env` 中的 `POSTGRES_PASSWORD` 创建用户。后续即使你改了 `.env`，数据库内部密码不会自动更新。

如果日志出现 `password authentication failed for user "postgres"`，按下面处理：

```bash
# 把库内 postgres 用户密码同步为新值（替换 YourNewPassword）
docker exec -u postgres german-db psql -d sitp_german_ai_agent -c \
  "ALTER USER postgres WITH PASSWORD 'YourNewPassword';"

# 重启后端以重新建立连接
docker compose restart backend
docker compose logs -f backend
```

升级后建议执行验证：

```bash
# 服务状态
docker compose ps

# 链路探活（返回 401 或 200 都表示链路打通；502 表示后端未就绪）
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"TestPassword"}'
```

#### 升级部署可选：一键改密脚本（Shell + Python）

```bash
#!/bin/bash
# 此脚本完成：改 .env、同步 DB、更新业务账号、验证

set -e

# 1. 更新 .env
NEW_DB_PASS="NewDbPassword_2026!"
NEW_ADMIN_PASS="NewAdminPassword_2026!"

# 备份原 .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# 修改密码行（Linux/Mac）
sed -i.bak "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_DB_PASS/" .env
sed -i.bak "s/^INIT_ADMIN_PASSWORD=.*/INIT_ADMIN_PASSWORD=$NEW_ADMIN_PASS/" .env

# Windows PowerShell
# (Get-Content .env) -replace 'POSTGRES_PASSWORD=.*', "POSTGRES_PASSWORD=$NEW_DB_PASS" | Set-Content .env
# (Get-Content .env) -replace 'INIT_ADMIN_PASSWORD=.*', "INIT_ADMIN_PASSWORD=$NEW_ADMIN_PASS" | Set-Content .env

# 2. 同步数据库 postgres 用户密码
docker exec -u postgres german-db psql -d sitp_german_ai_agent -c \
  "ALTER USER postgres WITH PASSWORD '$NEW_DB_PASS';"

# 3. 重启后端以应用新密码
docker compose restart backend

# 等待后端就绪
sleep 5

# 4. 创建 Python 脚本以更新业务账号
cat > /tmp/update_passwords.py << 'EOF'
import os
import sys
os.environ['SQLALCHEMY_DATABASE_URL'] = f"postgresql://postgres:{os.environ['POSTGRES_PASSWORD']}@localhost:5432/{os.environ['POSTGRES_DB']}"
sys.path.insert(0, '/app')
from backend.crud.repositories import UserCRUD
from backend.core.password import hash_password
from backend.db.session import SessionLocal

session = SessionLocal()
new_admin_pass = os.environ.get('INIT_ADMIN_PASSWORD')

try:
    admin_user = UserCRUD.get_by_username(session, 'admin')
    if admin_user:
        admin_user.hashed_password = hash_password(new_admin_pass)
        session.commit()
        print("✅ Admin password updated")
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    session.close()
EOF

# 5. 在后端容器内执行密码更新
docker compose exec -T backend python /tmp/update_passwords.py

# 6. 验证登录
echo "Testing login..."
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"$NEW_ADMIN_PASS\"}"

echo "✅ Password update complete!"
```

#### 常见启动问题速查

| 错误现象                                                       | 根本原因                           | 解决方案                                         |
| -------------------------------------------------------------- | ---------------------------------- | ------------------------------------------------ |
| `required variable POSTGRES_PASSWORD is missing`               | `.env` 缺少 `POSTGRES_PASSWORD`    | 补齐该变量后重新 `docker compose up -d --build`  |
| 后端日志：`password authentication failed for user "postgres"` | `.env` 与数据库内部密码不一致      | 按上文"场景 B"执行 `ALTER USER` 同步密码         |
| 前端返回 `502 Bad Gateway`                                     | Nginx 无法连接后端容器或后端未就绪 | 查看 backend 日志：`docker compose logs backend` |
| 系统正常启动但 AI 对话无回复                                   | LLM 配置错误或 API Key 无效        | 检查 LLM_PROVIDER、QWEN_API_KEY、LMSTUDIO 连接   |

#### 第 6 步：日志查看与故障诊断

```bash
# 查看所有容器实时日志
docker compose logs -f

# 仅查看后端日志（排查 DB 连接、API 错误）
docker compose logs -f backend

# 仅查看前端日志（排查 Nginx 反代错误）
docker compose logs -f frontend

# 仅查看数据库日志
docker compose logs -f db

# 查看最近 N 行日志
docker compose logs --tail 100 backend

# 查看指定时间段日志（近 1 小时）
docker compose logs --since 1h backend
```

**常见日志特征：**

| 关键字                                | 含义                       | 处理                                             |
| ------------------------------------- | -------------------------- | ------------------------------------------------ |
| `password authentication failed`      | PostgreSQL 用户认证失败    | 检查 POSTGRES_PASSWORD 与容器内密码一致性        |
| `Connection to localhost:5432 failed` | 后端连接数据库超时或被拒绝 | 检查 DB 容器是否运行、POSTGRES_PASSWORD 是否正确 |
| `502 Bad Gateway` (Nginx 日志)        | 反向代理无法连接后端       | 检查后端容器是否运行、端口是否正确               |
| `Application startup complete`        | 后端启动成功               | 系统就绪                                         |

#### 第 7 步：停止、重启、清理

```bash
# 重启所有容器（保留数据卷）
docker compose restart

# 停止所有容器（不删除）
docker compose down

# 停止并删除容器、卷（谨慎！会删除数据库数据）
docker compose down -v

# 强制删除容器并重建（完全重新部署）
docker system prune -a --volumes -f && docker compose up -d --build
```

---

### 💻 本地开发环境快速启动

适用需要于需要修改代码并实时预览开发的开发场景。

> **前置要求**：Node.js ≥ 18、Python ≥ 3.10、正在运行的 PostgreSQL 16 实例、根目录下.env环境配置文件

**1. 启动数据库**

可使用 Docker 单独启动 PostgreSQL：

```bash
docker compose up -d db
```

> 说明：本项目数据库结构由 Alembic 统一管理，本地开发不再需要手工执行 `backend/db/sql` 下的 SQL 文件。

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

# 执行数据库迁移
alembic -c alembic.ini upgrade head

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

| 现象                     | 常见原因                                 | 处理方式                                                                                              |
| ------------------------ | ---------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| AI 对话无响应 / 超时     | LM Studio 服务未启动                     | 在 LM Studio 中重新启动本地 API 服务                                                                  |
| 后端报 404               | `LMSTUDIO_BASE_URL` 配错（缺端口或路径） | 使用 `http://127.0.0.1:1234` 或 `http://host.docker.internal:1234`，不要手动拼 `/v1/chat/completions` |
| Docker 模式连接失败      | 容器内写成了 `127.0.0.1`                 | 改为 `host.docker.internal`                                                                           |
| 模型调用报错             | `LMSTUDIO_MODEL` 与当前加载模型名不一致  | 在 LM Studio 中复制准确模型 ID 到 `.env`                                                              |
| 切换 provider 后行为异常 | 后端未重启，仍使用旧环境变量             | 重启后端服务（本地重启 uvicorn / Docker 重启 backend）                                                |

---

### 演示账号

系统首次启动时会自动初始化以下演示账号（含多班级样例）。
账号名固定，但密码不再在后端硬编码：

- 教师演示账号密码来自 `.env` 的 `DEMO_TEACHER_PASSWORD`
- 学生演示账号密码来自 `.env` 的 `DEMO_STUDENT_PASSWORD`
- 管理员账号密码来自 `.env` 的 `INIT_ADMIN_PASSWORD`
- 若未配置上述密码，系统会为“新建账号”生成随机强密码并输出到后端日志

| 角色   | 用户名/学号 | 密码                | 班级                        | 备注   |
| ------ | ----------- | ------------------- | --------------------------- | ------ |
| 教师   | `t_zhang`   | `TeacherDemo@2026!` | 软件工程(四)班（SE-2026-4） | 张老师 |
| 学生   | `2452001`   | `StudentDemo@2026!` | 软件工程(四)班（SE-2026-4） | 李娜   |
| 学生   | `2452002`   | `StudentDemo@2026!` | 软件工程(四)班（SE-2026-4） | 王强   |
| 管理员 | `admin`     | `admin123`          | -                           | 管理员 |

> ⚠️ 教师端和学生端均已启用密码校验与权限隔离，学生账号无法访问教师端功能，反之亦然。

### 密码与认证说明

- 前端传输：登录与改密请求对密码执行 `SHA-256` 后再传输。
- 后端存储：统一存储为 `bcrypt(sha256(password))`，并兼容历史旧数据自动迁移。
- 管理员能力：管理员可在管理端重置教师/学生账号密码。
- 鉴权令牌：后端已改为 HMAC 签名令牌；更新后原有登录态会失效，需重新登录。

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

| 运行模式         | 启动方式                       | 前端访问地址     | API 请求路由                    |
| ---------------- | ------------------------------ | ---------------- | ------------------------------- |
| 🖥️ 本地开发      | `npm run dev`                  | `localhost:5173` | Vite Proxy → `localhost:8000`   |
| 🐳 本地 Docker   | `docker compose up -d --build` | `localhost:80`   | Nginx 反向代理 → `backend:8000` |
| 🌐 服务器 Docker | 同上 (在服务器执行)            | `服务器IP:80`    | Nginx 反向代理 → `backend:8000` |

**配置文件说明**

| 文件                              | 用途                                 | 是否提交到 Git |
| --------------------------------- | ------------------------------------ | -------------- |
| `frontend/.env.development`       | 开发模式默认配置（Proxy 目标地址等） | ✅ 是          |
| `frontend/.env.production`        | 生产模式默认配置                     | ✅ 是          |
| `frontend/.env.development.local` | **本地覆盖**（如需代理到远程服务器） | ❌ 否          |

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

| 方法     | 端点                                  | 功能                     |
| -------- | ------------------------------------- | ------------------------ |
| `POST`   | `/api/auth/login`                     | 教师/管理员登录          |
| `POST`   | `/api/auth/student-login`             | 学生登录                 |
| `PUT`    | `/api/user/password`                  | 教师/学生自助修改密码    |
| `GET`    | `/api/admin/teachers`                 | 管理员查看教师列表       |
| `PUT`    | `/api/admin/teachers/{user_id}`       | 管理员更新教师状态与启停 |
| `DELETE` | `/api/admin/teachers/{user_id}`       | 管理员删除教师账号       |
| `GET`    | `/api/admin/students`                 | 管理员查看学生列表       |
| `PUT`    | `/api/admin/students/{student_id}`    | 管理员更新学生信息       |
| `DELETE` | `/api/admin/students/{student_id}`    | 管理员删除学生账号       |
| `PUT`    | `/api/admin/users/{user_id}/password` | 管理员重置教师/学生密码  |
| `GET`    | `/api/admin/classes`                  | 管理员查看班级列表       |
| `POST`   | `/api/admin/classes`                  | 管理员创建班级           |
| `PUT`    | `/api/admin/classes/{class_id}`       | 管理员编辑班级           |
| `DELETE` | `/api/admin/classes/{class_id}`       | 管理员删除班级           |
| `PUT`    | `/api/admin/system/settings`          | 管理员更新审核策略       |
| `GET`    | `/api/teacher/dashboard`              | 教师教学仪表盘           |
| `GET`    | `/api/teacher/students`               | 教师查看班内学生         |
| `POST`   | `/api/scenario/publish`               | 教师发布情景任务         |
| `POST`   | `/api/exam/generate`                  | 教师生成智能试卷         |
| `GET`    | `/api/student/favorites/list`         | 学生查看收藏列表         |
| `DELETE` | `/api/student/favorites/{fav_id}`     | 学生删除收藏             |
| `GET`    | `/api/student/learning/progress`      | 学生学习进度总览         |

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
