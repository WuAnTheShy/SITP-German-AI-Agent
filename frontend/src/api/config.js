// ---------------------------------------------------------------
// 统一 API 配置
// ---------------------------------------------------------------
// 开发模式下：Vite proxy 会将 /api 请求代理到 http://localhost:8000
// 生产模式下：Nginx 会将 /api 请求反向代理到后端容器
// 因此 API_BASE 设为空字符串即可，所有请求都走相对路径 /api/xxx
// ---------------------------------------------------------------

export const API_BASE = '';

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
