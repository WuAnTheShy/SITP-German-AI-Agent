-- SITP German AI Agent
-- PostgreSQL Schema V1
-- 目标：支撑教师端核心流程 + 学生基础画像/作业链路

BEGIN;

-- 1) 账号主表
CREATE TABLE IF NOT EXISTS users (
    id              BIGSERIAL PRIMARY KEY,
    username        VARCHAR(64) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(16) NOT NULL CHECK (role IN ('teacher', 'student')),
    display_name    VARCHAR(64) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2) 班级表
CREATE TABLE IF NOT EXISTS classes (
    id              BIGSERIAL PRIMARY KEY,
    class_code      VARCHAR(32) NOT NULL UNIQUE,
    class_name      VARCHAR(128) NOT NULL,
    grade           VARCHAR(32),
    teacher_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3) 学生档案
CREATE TABLE IF NOT EXISTS students (
    id              BIGSERIAL PRIMARY KEY,
    uid             VARCHAR(32) NOT NULL UNIQUE,
    user_id         BIGINT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    class_id        BIGINT NOT NULL REFERENCES classes(id) ON DELETE RESTRICT,
    name            VARCHAR(64) NOT NULL,
    active_score    INTEGER NOT NULL DEFAULT 0 CHECK (active_score BETWEEN 0 AND 100),
    overall_score   NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (overall_score BETWEEN 0 AND 100),
    weak_point      VARCHAR(128),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4) 学生能力画像（1:1）
CREATE TABLE IF NOT EXISTS student_abilities (
    id              BIGSERIAL PRIMARY KEY,
    student_id      BIGINT NOT NULL UNIQUE REFERENCES students(id) ON DELETE CASCADE,
    listening       INTEGER NOT NULL DEFAULT 0 CHECK (listening BETWEEN 0 AND 100),
    speaking        INTEGER NOT NULL DEFAULT 0 CHECK (speaking BETWEEN 0 AND 100),
    reading         INTEGER NOT NULL DEFAULT 0 CHECK (reading BETWEEN 0 AND 100),
    writing         INTEGER NOT NULL DEFAULT 0 CHECK (writing BETWEEN 0 AND 100),
    ai_diagnosis    TEXT,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5) 作业记录
CREATE TABLE IF NOT EXISTS homeworks (
    id              BIGSERIAL PRIMARY KEY,
    student_id      BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    title           VARCHAR(255) NOT NULL,
    status          VARCHAR(32) NOT NULL DEFAULT '未提交' CHECK (status IN ('已完成', '待订正', '未提交', '进行中', '逾期补交')),
    submitted_at    TIMESTAMPTZ,
    score           NUMERIC(5,2) CHECK (score BETWEEN 0 AND 100),
    file_type       VARCHAR(16) CHECK (file_type IN ('audio', 'text', 'pdf', 'doc', 'other')),
    file_url        TEXT,
    file_name       VARCHAR(255),
    file_size       VARCHAR(64),
    ai_comment      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6) 人工评分流水（保留历史）
CREATE TABLE IF NOT EXISTS homework_reviews (
    id              BIGSERIAL PRIMARY KEY,
    homework_id     BIGINT NOT NULL REFERENCES homeworks(id) ON DELETE CASCADE,
    teacher_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    score           NUMERIC(5,2) NOT NULL CHECK (score BETWEEN 0 AND 100),
    feedback        TEXT,
    reviewed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7) 情景任务
CREATE TABLE IF NOT EXISTS scenarios (
    id                              BIGSERIAL PRIMARY KEY,
    scenario_code                   VARCHAR(32) NOT NULL UNIQUE,
    teacher_user_id                 BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    theme                           VARCHAR(128) NOT NULL,
    difficulty                      VARCHAR(64) NOT NULL,
    persona                         VARCHAR(64) NOT NULL,
    goal_require_perfect_tense      BOOLEAN NOT NULL DEFAULT FALSE,
    goal_require_b1_vocab           BOOLEAN NOT NULL DEFAULT FALSE,
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8) 情景任务推送记录
CREATE TABLE IF NOT EXISTS scenario_pushes (
    id              BIGSERIAL PRIMARY KEY,
    scenario_id     BIGINT NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    student_id      BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    push_status     VARCHAR(32) NOT NULL DEFAULT 'pushed',
    pushed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (scenario_id, student_id)
);

-- 9) 试卷生成记录
CREATE TABLE IF NOT EXISTS exams (
    id              BIGSERIAL PRIMARY KEY,
    exam_code       VARCHAR(32) NOT NULL UNIQUE,
    teacher_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    grammar_items   INTEGER NOT NULL CHECK (grammar_items >= 0),
    writing_items   INTEGER NOT NULL CHECK (writing_items >= 0),
    strategy        VARCHAR(32) NOT NULL CHECK (strategy IN ('personalized', 'unified')),
    focus_areas     JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 10) 试卷分发记录
CREATE TABLE IF NOT EXISTS exam_assignments (
    id              BIGSERIAL PRIMARY KEY,
    exam_id         BIGINT NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    student_id      BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    assigned_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status          VARCHAR(32) NOT NULL DEFAULT 'assigned',
    UNIQUE (exam_id, student_id)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_students_uid ON students(uid);
CREATE INDEX IF NOT EXISTS idx_students_class_id ON students(class_id);
CREATE INDEX IF NOT EXISTS idx_homeworks_student_id ON homeworks(student_id);
CREATE INDEX IF NOT EXISTS idx_homework_reviews_homework_id ON homework_reviews(homework_id);
CREATE INDEX IF NOT EXISTS idx_scenarios_teacher_user_id ON scenarios(teacher_user_id);
CREATE INDEX IF NOT EXISTS idx_exams_teacher_user_id ON exams(teacher_user_id);

COMMIT;
