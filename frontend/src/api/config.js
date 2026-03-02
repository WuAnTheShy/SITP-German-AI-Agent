// ---------------------------------------------------------------
// 统一 API 配置
// ---------------------------------------------------------------
// 自动读取环境变量（需要配置 Vite .env 文件）
// 开发模式 (.env.development)：VITE_API_BASE=http://localhost:8000
// 生产模式 (.env.production默认)：VITE_API_BASE= 空字符串（由反向代理决定）
// ---------------------------------------------------------------

// eslint-disable-next-line
export const API_BASE = import.meta.env.VITE_API_BASE ?? '';

// ---- 认证 ----
export const API_LOGIN = `${API_BASE}/api/auth/login`;

// ---- 教师仪表盘 ----
export const API_DASHBOARD = `${API_BASE}/api/teacher/dashboard`;

// ---- 情景任务 ----
export const API_SCENARIO_PUBLISH = `${API_BASE}/api/scenario/publish`;

// ---- 试卷生成 ----
export const API_EXAM_GENERATE = `${API_BASE}/api/exam/generate`;

// ---- 学生详情 ----
export const API_STUDENT_DETAIL = `${API_BASE}/api/student/detail`;

// ---- 作业 ----
export const API_HOMEWORK_DETAIL = `${API_BASE}/api/homework/detail`;
export const API_HOMEWORK_SAVE = `${API_BASE}/api/homework/save`;

// ---- 推送方案 ----
export const API_PUSH_SCHEME = `${API_BASE}/api/student/push-scheme`;
