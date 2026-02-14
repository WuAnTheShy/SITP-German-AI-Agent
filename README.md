# AI 智能体辅助大学德语个性化学习路径探究 (SITP-German-AI-Agent)

> 同济大学大学生创新训练项目 (SITP) - 校级项目

## 📖 项目背景与研究内容 (Research Context)

在传统的大学德语教学模式中，往往面临着课堂练习时间有限、难以兼顾每位学生的个性化需求等痛点。为了突破这些局限，本项目致力于设计并实现适应大学德语课堂的 **智能体 (AI Agent)**，通过技术与教学的深度融合，重塑课堂生态。

### 核心研究目标

本课题的核心在于打破传统的“教师-学生”二元结构，构建 **“教师-学生-机器” (Teacher-Student-AI)** 的三元协同教学新模式。

### 主要功能逻辑

1. **学生端 (Student Perspective): 个性化伴学**

  - 为每位学生创建**个性化智能体**，学生可根据自身水平和需求与 AI 进行 1-on-1 的交流学习。
  - 系统支持**差异化资源推送**，根据学生的学习数据生成个性化学习方案，涵盖听、说、读、写全方位训练。
  - **弥补传统教学不足**，让学生在课后也能获得高质量的语言输入与产出环境，引领学生在外语学习中不断进步。

2. **教师端 (Teacher Perspective): 智能助教与学情洞察**

  - 通过智能体驱动的**智能陪练**和**情景模拟**活动，教师可以实时掌握全班总体情况及个体的薄弱环节。
  - 强化学生的**语言产出**与**实际应用训练**，重点提升跨文化沟通能力。
  - **自动化教学资源生成**：针对学生情况自动生成不同难度的语言、词汇及语法练习和试卷，用于检验或巩固所学，实现“事半功倍”的教学效果。

## 🛠 技术栈 (Tech Stack)

本项目采用现代化的前后端分离架构与容器化部署方案：

### 前端 (Frontend)

- **构建工具**: [Vite](https://vitejs.dev/)
- **核心框架**: [React 19](https://react.dev/)
- **UI 组件库**: [Ant Design (v6)](https://ant.design/)
- **样式方案**: [Tailwind CSS](https://tailwindcss.com/)
- **路由管理**: [React Router v7](https://reactrouter.com/)
- **HTTP 请求**: Axios

### 后端 (Backend)

- **Web 框架**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **AI 模型**: Google Gemini (通过 `google-generativeai` SDK)
- **服务器**: Uvicorn

### 基础设施 (DevOps)

- **容器化**: Docker & Docker Compose
- **CI/CD**: GitHub Actions (自动部署至 GitHub Pages)

## 📂 项目结构 (Structure)

```
/
├── frontend/            # 前端 React 项目代码
│   ├── src/             # 页面与组件源码
│   ├── Dockerfile       # 前端镜像构建文件
│   └── ...
├── backend/             # 后端 Python 项目代码
│   ├── main.py          # 后端入口文件
│   ├── Dockerfile       # 后端镜像构建文件
│   └── requirements.txt # Python 依赖列表
├── docker-compose.yml   # 容器编排文件 (一键启动)
├── .github/             # GitHub Actions 自动化部署配置
├── README.md            # 项目 README 文档
└── .env                 # 环境变量配置文件 (需手动创建)
```

## 🐳 Docker 快速启动 (推荐)

这是最简单的运行方式，无需在本地安装 Node.js 或 Python 环境，只需安装 Docker。

### 1. 环境准备

确保已安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/) 并启动。

### 2. 配置密钥

在项目根目录下创建一个 `.env` 文件，填入你的 Google Gemini API Key：

```
GOOGLE_API_KEY=你的_Google_Gemini_API_密钥
```

### 3. 一键启动

在项目根目录打开终端，运行：

```
docker-compose up -d --build
```

- `-d`: 后台运行
- `--build`: 强制重新构建镜像（当代码有修改时推荐加上）

### 4. 访问服务

启动成功后，即可访问：

- **前端页面**: [http://localhost](https://www.google.com/search?q=http://localhost)
- **后端 API 文档**: [http://localhost:8000/docs](https://www.google.com/search?q=http://localhost:8000/docs)

### 常用命令

```
# 查看日志 (排查错误)
docker-compose logs -f

# 停止并删除容器
docker-compose down
```

## 💻 本地开发 (Manual Setup)

如果你不使用 Docker，也可以分别手动启动前后端。

### 1. 启动后端 (Backend)

```
cd backend
# 创建虚拟环境 (可选，但推荐)
python -m venv venv
# Windows 激活虚拟环境: .\venv\Scripts\activate
# Mac/Linux 激活虚拟环境: source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 设置 API Key (或者直接写在环境变量里)
export GOOGLE_API_KEY=你的密钥  # Windows (CMD): set GOOGLE_API_KEY=你的密钥

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 启动前端 (Frontend)

```
cd frontend
# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

*注意：手动启动时，前端默认访问 `http://localhost:5173`，请确保代码中的 API 请求地址指向正确的后端端口 (8000)。*

## 👥 项目团队 (Team)

| **角色**       | **姓名** | **学院**             | **分工**                       |
| -------------- | -------- | -------------------- | :----------------------------- |
| **指导教师**   | 汤春艳   | 外国语学院           | 教学理论指导、资源支持         |
| **项目负责人** | 魏世杰   | 计算机科学与技术学院 | 系统架构设计、服务器部署与维护 |
| **核心成员**   | 洪超慧   | 中德工程学院         | 前端界面——学生端               |
| **核心成员**   | 童文景   | 计算机科学与技术学院 | 前端界面——教师端               |
| **核心成员**   | 周雨晗   | 外国语学院           | 德语语料搜集、数据库输入       |
| **核心成员**   | 王莹     | 计算机科学与技术学院 | AI 智能体搭建                  |
