import axios from 'axios';
import { API_BASE } from './config';

// ---------------------------------------------------------------
// 统一 axios 实例
// ---------------------------------------------------------------
// - 自动携带 authToken（从 localStorage 读取）
// - 统一响应拦截：401 自动跳转登录页

const request = axios.create({
    baseURL: API_BASE,
    timeout: 15000,
});

// 请求拦截器 — 注入 Token
request.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('authToken');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// 响应拦截器 — 401 自动跳转
request.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('authToken');
            localStorage.removeItem('userInfo');
            // 使用 HashRouter 格式跳转
            window.location.hash = '#/teacher/login';
        }
        return Promise.reject(error);
    }
);

export default request;
