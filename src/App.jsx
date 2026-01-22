// 文件路径: src/App.jsx
import React from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';

// 引入页面组件
import Login from './pages/Login';
import StudentHome from './pages/student/StudentHome';
import TeacherLogin from './pages/teacher/TeacherLogin'; // 新增
import TeacherDashboard from './pages/teacher/TeacherDashboard';

function App() {
    return (
        <HashRouter>
            <Routes>
                {/* 1. 首页：角色选择 */}
                <Route path="/" element={<Login />} />

                {/* 2. 学生端 */}
                <Route path="/student" element={<StudentHome />} />

                {/* 3. 教师端流程 */}
                <Route path="/teacher/login" element={<TeacherLogin />} /> {/* 登录页 */}
                <Route path="/teacher/dashboard" element={<TeacherDashboard />} /> {/* 仪表盘 */}
            </Routes>
        </HashRouter>
    );
}

export default App;