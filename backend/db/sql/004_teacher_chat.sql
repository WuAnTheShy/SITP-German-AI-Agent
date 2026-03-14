-- 教师端教研助手对话：按用户隔离，与学生 chat_sessions 分离（学生表绑定 student_id）
BEGIN;

CREATE TABLE IF NOT EXISTS teacher_chat_sessions (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS teacher_chat_messages (
    id              BIGSERIAL PRIMARY KEY,
    session_id      BIGINT        NOT NULL REFERENCES teacher_chat_sessions(id) ON DELETE CASCADE,
    role            VARCHAR(16)   NOT NULL CHECK (role IN ('user', 'assistant')),
    content         TEXT          NOT NULL,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_teacher_chat_sessions_user ON teacher_chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_teacher_chat_messages_session ON teacher_chat_messages(session_id);

COMMIT;
