# SITP German AI Agent 数据库设计文档（V1）

## 1. 文档目标

本文件用于给项目组冻结数据库设计方向，支持以下工作：

- 教师端 Mock 接口替换为本地真实接口
- 学生/教师数据统一入库
- 后续能力分析与教学闭环扩展

> 当前阶段目标：先支持“教师端核心流程 + 学生基础画像/作业链路”，AI 调用可先保持 Mock。

---

## 2. 设计范围（本期）

覆盖前端现有业务页面对应的数据需求：

- 教师登录
- 教师仪表盘
- 发布情景任务
- 生成试卷
- 学生详情
- 作业详情/评分保存
- 推送个性化方案

范围说明：

- **V1 主要从教师端流程出发**（登录、仪表盘、任务、试卷、评分、推送）。
- **涵盖学生端**，已纳入学生基础档案、能力画像、作业记录等核心数据。
- 学生端更细粒度模块（如错题本/收藏/完整聊天轨迹）放入后续版本扩展。

不包含（后续）：

- 语音文件处理流水线
- 复杂推荐算法中间特征库
- 全量聊天语义索引（可后续加向量库）

---

## 3. 接口设计（暂时冻结此版）

### 3.1 教师端

- `POST /api/auth/login`
- `GET /api/teacher/dashboard`
- `POST /api/scenario/publish`
- `POST /api/exam/generate`
- `GET /api/student/detail?id=...`
- `GET /api/homework/detail?id=...`
- `POST /api/homework/save`
- `POST /api/student/push-scheme`

### 3.2 学生端（暂时使用 Mock）

- `POST /api/chat`

---

## 4. 表结构清单

## 6.1 `users`（账号主表）

- `id` (PK)
- `username` (唯一)
- `password_hash`
- `role` (`teacher` / `student`)
- `display_name`
- `is_active`
- `created_at`, `updated_at`

## 6.2 `classes`（班级）

- `id` (PK)
- `class_code` (唯一)
- `class_name`
- `grade`
- `teacher_user_id` (FK -> users.id)
- `created_at`, `updated_at`

## 6.3 `students`（学生档案）

- `id` (PK)
- `uid` (学号，唯一，前端路由主键)
- `user_id` (FK -> users.id)
- `class_id` (FK -> classes.id)
- `name`
- `active_score`（活跃度）
- `overall_score`（综合分）
- `weak_point`（薄弱环节）
- `created_at`, `updated_at`

## 6.4 `student_abilities`（能力画像）

- `id` (PK)
- `student_id` (FK -> students.id, 唯一)
- `listening`
- `speaking`
- `reading`
- `writing`
- `ai_diagnosis`
- `updated_at`

## 6.5 `homeworks`（作业记录）

- `id` (PK)
- `student_id` (FK -> students.id)
- `title`
- `status`（已完成/未提交/待订正...）
- `submitted_at`
- `score`（可空，最终分）
- `file_type`（audio/text/...）
- `file_url`
- `file_name`
- `file_size`
- `ai_comment`
- `created_at`, `updated_at`

## 6.6 `homework_reviews`（人工评分流水）

- `id` (PK)
- `homework_id` (FK -> homeworks.id)
- `teacher_user_id` (FK -> users.id)
- `score`
- `feedback`
- `reviewed_at`

## 6.7 `scenarios`（情景任务）

- `id` (PK)
- `scenario_code`（业务展示ID，可读）
- `teacher_user_id` (FK -> users.id)
- `theme`
- `difficulty`
- `persona`
- `goal_require_perfect_tense` (bool)
- `goal_require_b1_vocab` (bool)
- `created_at`

## 6.8 `scenario_pushes`（任务推送记录）

- `id` (PK)
- `scenario_id` (FK -> scenarios.id)
- `student_id` (FK -> students.id)
- `push_status`
- `pushed_at`

## 6.9 `exams`（试卷生成记录）

- `id` (PK)
- `exam_code`（业务展示ID）
- `teacher_user_id` (FK -> users.id)
- `grammar_items`
- `writing_items`
- `strategy`（personalized/unified）
- `focus_areas`（JSON）
- `created_at`

## 6.10 `exam_assignments`（试卷分发记录）

- `id` (PK)
- `exam_id` (FK -> exams.id)
- `student_id` (FK -> students.id)
- `assigned_at`
- `status`

---

## 5. 关系说明（类似ER）

- 一个教师（`users.role=teacher`）可以管理多个班级（`classes`）。
- 一个班级有多个学生（`students`）。
- 一个学生有一条能力画像（`student_abilities`，1:1）。
- 一个学生有多条作业（`homeworks`）。
- 一条作业可有多次评分记录（`homework_reviews`，保留历史）。
- 一个教师可发布多个情景任务（`scenarios`），任务可推送给多个学生（`scenario_pushes`）。
- 一个教师可生成多个试卷（`exams`），试卷可分发给多个学生（`exam_assignments`）。

---

## 6. 建表顺序建议

1. `users`
2. `classes`
3. `students`
4. `student_abilities`
5. `homeworks`
6. `homework_reviews`
7. `scenarios`
8. `scenario_pushes`
9. `exams`
10. `exam_assignments`

并在以下字段建索引：

- `students.uid`
- `students.class_id`
- `homeworks.student_id`
- `homework_reviews.homework_id`
- `scenarios.teacher_user_id`
- `exams.teacher_user_id`

---

## 7. 技术栈建议（数据库子系统）

- 数据库：PostgreSQL 16
- ORM：SQLAlchemy 2.x
- 迁移：Alembic
- 验证：Pydantic
- 服务：FastAPI（项目已在用）

---

## 8. 目录与代码位置（已实现）

- `db/`：连接、会话、迁移配置
- `models/`：ORM 模型
- `schemas/`：请求/响应模型
- `crud/`：数据库读写逻辑

关键文件：

- [backend/db/sql/001_init_schema.sql](backend/db/sql/001_init_schema.sql)
- [backend/db/sql/002_seed_demo.sql](backend/db/sql/002_seed_demo.sql)
- [backend/models/entities.py](backend/models/entities.py)
- [backend/schemas/entities.py](backend/schemas/entities.py)
- [backend/crud/repositories.py](backend/crud/repositories.py)
- [backend/main.py](backend/main.py)

---

## 9. 下一步执行清单（简版）

1. 项目组确认本文件中的 10 张表与字段命名。
2. 使用 SQL 脚本落库并执行种子数据。
3. 在 `/docs` 验证教师端 8 个接口返回 `code=200`。
4. 再决定是否切前端到本地后端联调。
