# AI 智能体辅助大学德语个性化学习路径探究 (SITP-German-AI-Agent)

> 同济大学大学生创新训练项目 (SITP) - 校级项目

## 📖 项目简介 (Introduction)

本项目旨在解决传统大学德语课堂中存在的“练习时间不足”与“难以满足个性化需求”两大痛点。通过引入生成式人工智能（Generative AI），我们构建了一个“师-生-机”三元结构的教学辅助系统，为每位学生提供定制化的学习路径和资源，同时辅助教师实时掌握学情。

**核心目标：**
* **个性化教学：** 为学生提供定制化的学习路径、智能陪练和差异化资源推荐。
* **自主学习支撑：** 利用 AI 智能体弥补课堂互动不足，支持语音、词汇及语法的深度自主练习。
* **教学反馈闭环：** 辅助教师生成练习与试卷，评估学生学习成果，实现精准教学干预。

## 🚀 功能特性 (Features)

### 学生端 (Student)
* **个性化 AI 智能体**：基于用户特性（兴趣、能力）的 1-on-1 德语对话与陪练。
* **智能推荐**：根据学习进度推送差异化的学习资源和任务。
* **自主练习**：涵盖发音、语法、词汇的针对性训练。

### 教师端 (Teacher)
* **学情监控**：了解班级总体情况及学生个体差异。
* **智能辅助**：自动生成不同难度的练习题和试卷。
* **情景模拟**：驱动智能陪练进行特定的教学情景活动。

## 🛠 技术栈 (Tech Stack)

本项目采用现代化的前端技术栈构建：

* **构建工具**: [Vite](https://vitejs.dev/)
* **核心框架**: [React 19](https://react.dev/)
* **UI 组件库**: [Ant Design (v6)](https://ant.design/)
* **样式方案**: [Tailwind CSS](https://tailwindcss.com/)
* **路由管理**: [React Router v7](https://reactrouter.com/)
* **图标库**: [Lucide React](https://lucide.dev/)
* **Markdown 渲染**: [React Markdown](https://github.com/remarkjs/react-markdown)
* **HTTP 请求**: Axios
* **AI 模型支持**: 计划接入 Claude 架构等生成式 AI 模型

## 👥 项目团队 (Team)

| 角色 | 姓名 | 学院 | 分工 |
| :--- | :--- | :--- | :--- |
| **指导教师** | 汤春艳 | 外国语学院 | 教学理论指导、资源支持 |
| **项目负责人** | 魏世杰 | 计算机科学与技术学院 | 系统架构设计、AI 智能体搭建 |
| **核心成员** | 洪超慧 | 中德工程学院 | 资料搜集、数据库构建、智能体搭建 |
| **核心成员** | 童文景 | 计算机科学与技术学院 | 智能体搭建、服务器部署 |
| **核心成员** | 周雨晗 | 外国语学院 | 德语语料搜集、数据库输入 |
| **核心成员** | 王莹 | 计算机科学与技术学院 | 服务器部署与维护 |

## 💻 本地开发 (Development)

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

### Prerequisites
Ensure you have Node.js installed.

### Installation & Run

```bash
# Clone the repository
git clone https://github.com/WuAnTheShy/SITP-German-AI-Agent.git

# Install dependencies
npm install
# Run project
npm run dev
