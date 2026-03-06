# SITP German AI Agent API 接口参考手册

> **基础路径 (Base URL)**: `http://localhost:8000/api`
> **认证方式**: Bearer Token (在请求头中加入 `Authorization: Bearer <token>`)

---

## 1. 认证接口 (Authentication)

| 方法 | 路径 | 描述 |
|---|---|---|
| `POST` | `/auth/login` | 教师登录（自动创建账号） |
| `POST` | `/auth/student-login` | 学生登录（自动创建账号） |

---

## 2. 教师端接口 (Teacher Side)

### 2.1 仪表盘与学生管理
- `GET /teacher/dashboard`: 获取班级全局统计指标与学生列表。
- `GET /student/detail?id={uid}`: 获取特定学生的全画像（含能力模型、诊断、作业、考试记录）。

### 2.2 情景任务与试卷
- `POST /scenario/publish`: 发布 AI 情景对话任务至全班。
- `POST /exam/generate`: 调用 AI 生成（统一或个性化）试卷并分发。
  - **Payload 示例**:
    ```json
    {
      "grammarItems": 15,
      "writingItems": 2,
      "strategy": "personalized",
      "focusAreas": ["Passiv", "Konjunktiv"]
    }
    ```
- `GET /teacher/exam/list`: 获取已发布的试卷历史。
- `GET /teacher/exam/{id}`: 获取试卷题目详情。

### 2.3 作业与批改
- `GET /homework/detail?id={id}`: 获取某份作业的具体内容（文件 URL 或 JSON 答案）。
- `GET /homework/download/{id}`: 下载格式化的答卷文本（针对 Exam 类型）。
- `POST /homework/save`: 教师保存评分与反馈意见。
- `POST /student/push-scheme`: 为学生推送 AI 生成的个性化强化方案。

---

## 3. 学生端接口 (Student Side)

### 3.1 任务系统
- `GET /student/tasks`: 获取待办与已完成的任务列表。
- `GET /student/exam/assignment/{id}`: 获取考试题目。
- `POST /student/exam/submit`: 提交试卷答案并自动评分。
  - **Payload 示例**:
    ```json
    {
      "assignment_id": 12,
      "answers": {
        "0": "A. werden / gebacken",
        "1": "B. habe",
        "writing_15": "Heute bin ich sehr glücklich..."
      }
    }
    ```
  - **Response 示例**:
    ```json
    {
      "code": 200,
      "message": "提交成功",
      "data": {
        "score": 85.5,
        "ai_comment": "整体表达流畅，注意虚拟式的变位..."
      }
    }
    ```
- `GET /student/exam/result/{id}`: 查看试卷结果与解析。

### 3.2 学习工具
- `GET /student/vocab/list`: 获取词汇列表（支持级别/主题过滤）。
- `POST /student/vocab/collect`: 收藏/取消收藏单词。
- `POST /student/vocab/generate`: 调用 AI 批量生成单词例句。
- `GET /student/grammar/categories`: 获取语法分类。
- `GET /student/grammar/exercises`: 获取某分类下的练习题。
- `POST /student/grammar/submit`: 提交语法练习答案。
- `GET /student/listening/materials`: 获取听力素材列表。
- `POST /student/speaking/evaluate`: 提交口语录音进行 AI 评估。
- `POST /student/writing/check`: AI 实时语病检查。
- `POST /student/writing/generate-sample`: AI 生成命题范文。

### 3.3 个性化数据
- `GET /student/error-book/list`: 查看错题记录。
- `POST /student/error-book/mark-mastered`: 将错题标记为已掌握。
- `GET /student/learning/progress`: 获取学习时长统计与掌握度矩阵。
- `GET /student/favorites/list`: 查看收藏夹。

---

## 4. 公共/AI 接口
- `POST /chat`: 教师端 AI 教研对话入口。
- `POST /student/chat`: 学生端 AI 自由导师对话入口。
- `POST /student/scene-chat`: 学生端情景任务对话入口（带上下文）。

---

## 5. 错误代码说明
- `200`: 成功。
- `401`: 未授权或 Token 过期。
- `403`: 权限不足（如学生尝试访问教师接口）。
- `404`: 资源不存在。
- `500`: 服务器内部错误（通常伴随 `message` 字段描述具体异常）。
