# Database Local Setup (V1)

本目录用于数据库第一版落地（PostgreSQL）。

## 文件说明

- sql/001_init_schema.sql：初始化表结构与索引
- sql/002_seed_demo.sql：本地演示数据
- sql/003_student_schema.sql：学生端 V2 表（含 chat_sessions / chat_messages）
- sql/004_teacher_chat.sql：教师教研助手对话表（按用户隔离；也可由后端启动时自动创建）
- sql/005_agent_memory.sql：会话 closed_at/updated_at、师生长期摘要列（启动时亦会自动补丁）

## FastAPI 代码骨架（已创建）

- db/base.py：SQLAlchemy Base
- db/session.py：数据库连接与 `get_db()`
- db/init_db.py：`create_all_tables()`（开发阶段可直接建表）
- models/entities.py：10 张表对应 ORM 模型
- schemas/entities.py：10 张表对应 Pydantic 模型
- crud/repositories.py：10 张表对应 CRUD 基础方法

## 执行顺序

1. 先执行 `001_init_schema.sql`
2. 再执行 `002_seed_demo.sql`

## 说明

- 本版以教师端核心链路为主，同时包含学生基础画像/作业数据。
- 学生端高级功能（错题本、收藏、完整学习轨迹）可在 V2 扩展。
