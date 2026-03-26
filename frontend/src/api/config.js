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

export const API_ADMIN_TEACHERS = `${API_BASE}/api/admin/teachers`;
export const API_ADMIN_CLASSES = `${API_BASE}/api/admin/classes`;
export const API_ADMIN_SETTINGS = `${API_BASE}/api/admin/system/settings`;
export const API_ADMIN_PENDING_TEACHERS = `${API_BASE}/api/admin/users/pending-teachers`;
export const API_ADMIN_APPROVE_TEACHER = (id) => `${API_BASE}/api/admin/users/teachers/${id}/approve`;
export const API_ADMIN_REJECT_TEACHER = (id) => `${API_BASE}/api/admin/users/teachers/${id}/reject`;
export const API_ADMIN_DELETE_CLASS = (id) => `${API_BASE}/api/admin/classes/${id}`;
export const API_ADMIN_UPDATE_TEACHER = (id) => `${API_BASE}/api/admin/teachers/${id}`;
export const API_ADMIN_DELETE_TEACHER = (id) => `${API_BASE}/api/admin/teachers/${id}`;
export const API_ADMIN_STUDENTS = `${API_BASE}/api/admin/students`;
export const API_ADMIN_UPDATE_STUDENT = (id) => `${API_BASE}/api/admin/students/${id}`;
export const API_ADMIN_DELETE_STUDENT = (id) => `${API_BASE}/api/admin/students/${id}`;
export const API_ADMIN_RESET_USER_PASSWORD = (id) => `${API_BASE}/api/admin/users/${id}/password`;
export const API_ADMIN_KB_DOCS = `${API_BASE}/api/admin/kb/docs`;
export const API_ADMIN_KB_UPLOAD = `${API_BASE}/api/admin/kb/upload`;
export const API_ADMIN_KB_REINDEX = `${API_BASE}/api/admin/kb/reindex`;
export const API_ADMIN_KB_DELETE_DOC = (id) => `${API_BASE}/api/admin/kb/docs/${id}`;

// ---- 注册 ----
export const API_STUDENT_REGISTER = `${API_BASE}/api/auth/student-register`;
export const API_TEACHER_REGISTER = `${API_BASE}/api/auth/teacher-register`;

// ---- 学生：加入班级 ----
export const API_STUDENT_CLASSES = `${API_BASE}/api/student/classes`;
export const API_STUDENT_JOIN_CLASS = `${API_BASE}/api/student/join-class`;
export const API_USER_KB_DOCS = `${API_BASE}/api/user/kb/docs`;
export const API_USER_KB_UPLOAD = `${API_BASE}/api/user/kb/upload`;
export const API_USER_KB_REINDEX = `${API_BASE}/api/user/kb/reindex`;
export const API_USER_KB_DELETE = `${API_BASE}/api/user/kb/docs`;

// ---- 教师仪表盘 & 学生审批 ----
export const API_DASHBOARD = `${API_BASE}/api/teacher/dashboard`;
export const API_TEACHER_PENDING_STUDENTS = `${API_BASE}/api/teacher/pending-students`;
export const API_TEACHER_APPROVE_STUDENT = (id) => `${API_BASE}/api/teacher/students/${id}/approve`;
export const API_TEACHER_REJECT_STUDENT = (id) => `${API_BASE}/api/teacher/students/${id}/reject`;
export const API_TEACHER_STUDENTS = `${API_BASE}/api/teacher/students`;
export const API_TEACHER_UPDATE_STUDENT = (id) => `${API_BASE}/api/teacher/students/${id}`;
export const API_TEACHER_REMOVE_STUDENT = (id) => `${API_BASE}/api/teacher/students/${id}`;

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
export const API_FAVORITES_ADD = `${API_BASE}/api/student/favorites/add`;
export const API_FAVORITES_AI_EXTEND = `${API_BASE}/api/student/favorites/ai-extend`;
