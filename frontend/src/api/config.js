// ---------------------------------------------------------------
// 统一 API 配置
// ---------------------------------------------------------------
// 通过 Vite 环境变量 VITE_API_BASE_URL 控制 API 基础路径：
//
//   本地开发 (npm run dev)  → 空字符串，走 Vite Proxy
//   Docker 部署 (生产构建) → 空字符串，走 Nginx 反向代理
//   直连远程后端          → 设为 http://远程IP:端口
//
// 三种模式下前端代码完全一致，无需手动修改。
// ---------------------------------------------------------------

export const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

// ---- 认证 ----
export const API_LOGIN = `${API_BASE}/api/auth/login`;
export const API_STUDENT_LOGIN = `${API_BASE}/api/auth/student-login`;

// ---- 管理员 ----
export const API_ADMIN_TEACHERS = `${API_BASE}/api/admin/teachers`;
export const API_ADMIN_CLASSES = `${API_BASE}/api/admin/classes`;
export const API_STUDENT_REGISTER = `${API_BASE}/api/auth/student-register`;
export const API_TEACHER_REGISTER = `${API_BASE}/api/auth/teacher-register`;

// ---- 学生：加入班级 ----
export const API_STUDENT_CLASSES = `${API_BASE}/api/student/classes`;
export const API_STUDENT_JOIN_CLASS = `${API_BASE}/api/student/join-class`;

// ---- 教师仪表盘 ----
export const API_DASHBOARD = `${API_BASE}/api/teacher/dashboard`;

// ---- 情景任务 ----
export const API_SCENARIO_PUBLISH = `${API_BASE}/api/scenario/publish`;
export const API_TEACHER_SCENARIO_LIST = `${API_BASE}/api/teacher/scenario/list`;

// ---- 试卷生成 ----
export const API_EXAM_GENERATE = `${API_BASE}/api/exam/generate`;
export const API_TEACHER_EXAM_LIST = `${API_BASE}/api/teacher/exam/list`;
export const API_TEACHER_EXAM_DETAIL = `${API_BASE}/api/teacher/exam`; // /{exam_id}

// ---- 学生详情 ----
export const API_STUDENT_DETAIL = `${API_BASE}/api/student/detail`;

// ---- 作业 ----
export const API_HOMEWORK_DETAIL = `${API_BASE}/api/homework/detail`;
export const API_HOMEWORK_SAVE = `${API_BASE}/api/homework/save`;

// ---- 推送方案 ----
export const API_PUSH_SCHEME = `${API_BASE}/api/student/push-scheme`;

// ---- AI 对话 ----
export const API_CHAT = `${API_BASE}/api/chat`; // 教师专用
export const API_STUDENT_CHAT = `${API_BASE}/api/student/chat`; // 学生专用
export const API_STUDENT_CHAT_NEW = `${API_BASE}/api/student/chat/new-session`;
export const API_STUDENT_CHAT_SESSIONS = `${API_BASE}/api/student/chat/sessions`;
export const API_STUDENT_CHAT_MESSAGES = `${API_BASE}/api/student/chat/messages`;
export const API_STUDENT_CHAT_SESSION = `${API_BASE}/api/student/chat/session`;
export const API_TEACHER_CHAT_NEW = `${API_BASE}/api/teacher/chat/new-session`;
export const API_TEACHER_CHAT_SESSIONS = `${API_BASE}/api/teacher/chat/sessions`;
export const API_TEACHER_CHAT_MESSAGES = `${API_BASE}/api/teacher/chat/messages`;
export const API_TEACHER_CHAT_SESSION = `${API_BASE}/api/teacher/chat/session`;
export const API_SCENE_CHAT = `${API_BASE}/api/student/scene-chat`;
export const API_SCENE_CHAT_STATE = `${API_BASE}/api/student/scene-chat/state`;
export const API_SCENE_CHAT_CLEAR = `${API_BASE}/api/student/scene-chat/clear`;

// ---- 写作辅助 ----
export const API_WRITING_CHECK = `${API_BASE}/api/student/writing/check`;
export const API_WRITING_SAMPLE = `${API_BASE}/api/student/writing/generate-sample`;

// ---- 词汇学习 ----
export const API_VOCAB_LIST = `${API_BASE}/api/student/vocab/list`;
export const API_VOCAB_COLLECT = `${API_BASE}/api/student/vocab/collect`;
export const API_VOCAB_GENERATE = `${API_BASE}/api/student/vocab/generate`;

// ---- 语法练习 ----
export const API_GRAMMAR_CATEGORIES = `${API_BASE}/api/student/grammar/categories`;
export const API_GRAMMAR_EXERCISES = `${API_BASE}/api/student/grammar/exercises`;
export const API_GRAMMAR_SUBMIT = `${API_BASE}/api/student/grammar/submit`;

// ---- 听说训练 ----
export const API_LISTENING_MATERIALS = `${API_BASE}/api/student/listening/materials`;
export const API_LISTENING_DETAIL = `${API_BASE}/api/student/listening/material/detail`;
export const API_SPEAKING_EVALUATE = `${API_BASE}/api/student/speaking/evaluate`;

// ---- 学习进度 ----
export const API_LEARNING_PROGRESS = `${API_BASE}/api/student/learning/progress`;

// ---- 错题本 ----
export const API_ERROR_CATEGORIES = `${API_BASE}/api/student/error-book/categories`;
export const API_ERROR_LIST = `${API_BASE}/api/student/error-book/list`;
export const API_ERROR_START_REVIEW = `${API_BASE}/api/student/error-book/start-review`;
export const API_ERROR_MARK_MASTERED = `${API_BASE}/api/student/error-book/mark-mastered`;
export const API_ERROR_DELETE = `${API_BASE}/api/student/error-book/delete`;

// ---- 收藏夹 ----
export const API_FAVORITES_CATEGORIES = `${API_BASE}/api/student/favorites/categories`;
export const API_FAVORITES_LIST = `${API_BASE}/api/student/favorites/list`;
export const API_FAVORITES_DELETE = `${API_BASE}/api/student/favorites`;
export const API_FAVORITES_AI_EXTEND = `${API_BASE}/api/student/favorites/ai-extend`;
