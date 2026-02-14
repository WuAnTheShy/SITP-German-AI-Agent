# Database Local Setup (V1)

本目录用于数据库第一版落地（PostgreSQL）。

## 文件说明

- sql/001_init_schema.sql：初始化表结构与索引
- sql/002_seed_demo.sql：本地演示数据

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
