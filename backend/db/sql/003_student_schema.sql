-- ============================================================
-- SITP German AI Agent
-- PostgreSQL Schema V2 — 学生端功能扩展表
-- 在 001_init_schema.sql（V1 教师端）基础上新增 17 张表
-- 覆盖模块：场景对话 · 词汇 · 语法 · 听说 · 写作 · 错题 · 收藏 · 进度
-- ============================================================

BEGIN;

-- ============================================================
-- A. 场景对话模块 (AISceneChat)
-- ============================================================

-- A1) 对话场景字典
CREATE TABLE IF NOT EXISTS chat_scenes (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(128)  NOT NULL UNIQUE,
    description     TEXT,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- A2) 对话会话
CREATE TABLE IF NOT EXISTS chat_sessions (
    id              BIGSERIAL PRIMARY KEY,
    student_id      BIGINT        NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    scene_id        BIGINT        REFERENCES chat_scenes(id) ON DELETE SET NULL,
    scene_name      VARCHAR(128),
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- A3) 对话消息
CREATE TABLE IF NOT EXISTS chat_messages (
    id              BIGSERIAL PRIMARY KEY,
    session_id      BIGINT        NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role            VARCHAR(16)   NOT NULL CHECK (role IN ('user', 'assistant')),
    content         TEXT          NOT NULL,
    correction      TEXT,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ============================================================
-- B. 词汇学习模块 (VocabLearning)
-- ============================================================

-- B1) 词汇库
CREATE TABLE IF NOT EXISTS vocabularies (
    id              BIGSERIAL PRIMARY KEY,
    german          VARCHAR(255)  NOT NULL,
    chinese         VARCHAR(255)  NOT NULL,
    example         TEXT,
    level           VARCHAR(8)    NOT NULL DEFAULT 'A1'
                    CHECK (level IN ('A1','A2','B1','B2','C1','C2')),
    topic           VARCHAR(64)   NOT NULL DEFAULT '日常通用',
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    UNIQUE (german, level)
);

-- B2) 学生词汇收藏
CREATE TABLE IF NOT EXISTS student_vocab_collections (
    id              BIGSERIAL PRIMARY KEY,
    student_id      BIGINT        NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    vocab_id        BIGINT        NOT NULL REFERENCES vocabularies(id) ON DELETE CASCADE,
    collected_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    UNIQUE (student_id, vocab_id)
);

-- ============================================================
-- C. 语法练习模块 (GrammarPractice)
-- ============================================================

-- C1) 语法分类
CREATE TABLE IF NOT EXISTS grammar_categories (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(128)  NOT NULL UNIQUE,
    description     TEXT
);

-- C2) 语法练习题
CREATE TABLE IF NOT EXISTS grammar_exercises (
    id              BIGSERIAL PRIMARY KEY,
    category_id     BIGINT        NOT NULL REFERENCES grammar_categories(id) ON DELETE CASCADE,
    question        TEXT          NOT NULL,
    correct_answer  VARCHAR(512)  NOT NULL,
    analysis        TEXT
);

-- C3) 语法提交记录
CREATE TABLE IF NOT EXISTS grammar_submissions (
    id              BIGSERIAL PRIMARY KEY,
    student_id      BIGINT        NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    exercise_id     BIGINT        NOT NULL REFERENCES grammar_exercises(id) ON DELETE CASCADE,
    user_answer     VARCHAR(512)  NOT NULL,
    is_correct      BOOLEAN       NOT NULL,
    ai_analysis     TEXT,
    submitted_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ============================================================
-- D. 听说训练模块 (ListeningSpeaking)
-- ============================================================

-- D1) 听力材料
CREATE TABLE IF NOT EXISTS listening_materials (
    id              BIGSERIAL PRIMARY KEY,
    title           VARCHAR(255)  NOT NULL UNIQUE,
    level           VARCHAR(8)    NOT NULL DEFAULT 'A1'
                    CHECK (level IN ('A1','A2','B1','B2','C1','C2')),
    duration        VARCHAR(16)   NOT NULL DEFAULT '0:00',
    audio_url       TEXT          NOT NULL,
    script          TEXT,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- D2) 口语评估记录
CREATE TABLE IF NOT EXISTS speaking_evaluations (
    id                  BIGSERIAL PRIMARY KEY,
    student_id          BIGINT        NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    material_id         BIGINT        NOT NULL REFERENCES listening_materials(id) ON DELETE CASCADE,
    audio_url           TEXT,
    total_score         NUMERIC(5,2)  CHECK (total_score BETWEEN 0 AND 100),
    pronunciation_score NUMERIC(5,2)  CHECK (pronunciation_score BETWEEN 0 AND 100),
    fluency_score       NUMERIC(5,2)  CHECK (fluency_score BETWEEN 0 AND 100),
    intonation_score    NUMERIC(5,2)  CHECK (intonation_score BETWEEN 0 AND 100),
    analysis            TEXT,
    suggestion          TEXT,
    evaluated_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ============================================================
-- E. 写作辅助模块 (WritingAssistant)
-- ============================================================

CREATE TABLE IF NOT EXISTS writing_sessions (
    id              BIGSERIAL PRIMARY KEY,
    student_id      BIGINT        NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    session_type    VARCHAR(16)   NOT NULL
                    CHECK (session_type IN ('check', 'generate')),
    user_text       TEXT          NOT NULL,
    result_json     JSONB,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ============================================================
-- F. 错题本模块 (ErrorBookReview)
-- ============================================================

-- F1) 错题分类字典
CREATE TABLE IF NOT EXISTS error_book_categories (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(128)  NOT NULL UNIQUE
);

-- F2) 错题记录
CREATE TABLE IF NOT EXISTS error_book_entries (
    id              BIGSERIAL PRIMARY KEY,
    student_id      BIGINT        NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    category_id     BIGINT        NOT NULL REFERENCES error_book_categories(id) ON DELETE CASCADE,
    source          VARCHAR(64)   NOT NULL DEFAULT '语法练习',
    question        TEXT          NOT NULL,
    user_answer     TEXT          NOT NULL,
    correct_answer  TEXT          NOT NULL,
    analysis        TEXT,
    is_mastered     BOOLEAN       NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ============================================================
-- G. 收藏夹模块 (FavoritesPage)
-- ============================================================

-- G1) 收藏分类字典
CREATE TABLE IF NOT EXISTS favorite_categories (
    id              BIGSERIAL PRIMARY KEY,
    type            VARCHAR(32)   NOT NULL UNIQUE,
    name            VARCHAR(128)  NOT NULL
);

-- G2) 收藏记录
CREATE TABLE IF NOT EXISTS favorites (
    id              BIGSERIAL PRIMARY KEY,
    student_id      BIGINT        NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    category_id     BIGINT        NOT NULL REFERENCES favorite_categories(id) ON DELETE CASCADE,
    content         TEXT          NOT NULL,
    translate       TEXT,
    rule            TEXT,
    note            TEXT,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ============================================================
-- H. 学习进度模块 (LearningProgress)
-- ============================================================

-- H1) 学习时长记录
CREATE TABLE IF NOT EXISTS learning_sessions (
    id              BIGSERIAL PRIMARY KEY,
    student_id      BIGINT        NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    module          VARCHAR(64)   NOT NULL,
    duration_minutes INTEGER      NOT NULL DEFAULT 0 CHECK (duration_minutes >= 0),
    content         VARCHAR(255),
    session_date    DATE          NOT NULL DEFAULT CURRENT_DATE,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- H2) 知识点掌握度
CREATE TABLE IF NOT EXISTS student_knowledge_mastery (
    id              BIGSERIAL PRIMARY KEY,
    student_id      BIGINT        NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    knowledge_name  VARCHAR(128)  NOT NULL,
    mastery_level   VARCHAR(16)   NOT NULL DEFAULT '一般'
                    CHECK (mastery_level IN ('熟练', '一般', '薄弱')),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    UNIQUE (student_id, knowledge_name)
);

-- ============================================================
-- 索引
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_chat_sessions_student        ON chat_sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session         ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_vocab_level_topic             ON vocabularies(level, topic);
CREATE INDEX IF NOT EXISTS idx_student_vocab_coll_student    ON student_vocab_collections(student_id);
CREATE INDEX IF NOT EXISTS idx_grammar_ex_category           ON grammar_exercises(category_id);
CREATE INDEX IF NOT EXISTS idx_grammar_sub_student           ON grammar_submissions(student_id);
CREATE INDEX IF NOT EXISTS idx_listening_level               ON listening_materials(level);
CREATE INDEX IF NOT EXISTS idx_speaking_eval_student         ON speaking_evaluations(student_id);
CREATE INDEX IF NOT EXISTS idx_writing_sess_student          ON writing_sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_error_entries_student         ON error_book_entries(student_id);
CREATE INDEX IF NOT EXISTS idx_error_entries_category        ON error_book_entries(category_id);
CREATE INDEX IF NOT EXISTS idx_favorites_student             ON favorites(student_id);
CREATE INDEX IF NOT EXISTS idx_favorites_category            ON favorites(category_id);
CREATE INDEX IF NOT EXISTS idx_learn_sess_student            ON learning_sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_learn_sess_date               ON learning_sessions(session_date);
CREATE INDEX IF NOT EXISTS idx_knowledge_student             ON student_knowledge_mastery(student_id);

COMMIT;
