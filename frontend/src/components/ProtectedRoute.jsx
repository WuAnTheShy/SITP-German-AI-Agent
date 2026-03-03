import React from 'react';
import { Navigate, useLocation, useParams } from 'react-router-dom';

/**
 * 路由守卫组件
 * - 未登录 → 重定向到首页
 * - 角色不匹配 → 重定向到对应登录页
 *
 * @param {string} requiredRole - 'teacher' | 'student'
 * @param {React.ReactNode} children - 被保护的子组件
 */
const ProtectedRoute = ({ requiredRole, children }) => {
    const location = useLocation();
    const params = useParams();
    const token = localStorage.getItem('authToken');
    const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
    const userRole = userInfo.role;

    // 1. 未登录 → 回到首页
    if (!token) {
        return <Navigate to="/" replace state={{ from: location }} />;
    }

    // 2. 角色不匹配 → 跳转到对应登录页
    if (requiredRole && userRole !== requiredRole) {
        const redirectPath = userRole === 'student'
            ? '/student/login'
            : userRole === 'teacher'
                ? '/teacher/login'
                : '/';
        return <Navigate to={redirectPath} replace />;
    }

    // 3. 学生端 URL 的 userId 校验（确保每个人只能访问自己的页面）
    if (userRole === 'student' && params.userId) {
        // 当前登录学生的学号
        const loggedInUid = userInfo.id || userInfo.studentId;
        if (params.userId !== loggedInUid) {
            // 如果访问别人的页面，强制重定向到自己的页面
            const redirectPath = location.pathname.replace(`/student/${params.userId}`, `/student/${loggedInUid}`);
            return <Navigate to={redirectPath} replace />;
        }
    }

    // 4. 通过校验，渲染子组件
    return children;
};

export default ProtectedRoute;
