// 文件路径: src/App.jsx
import React from 'react';
// 1. 修改这里：把 BrowserRouter 改为 HashRouter
import { HashRouter, Routes, Route } from 'react-router-dom';

import Login from './pages/Login';

const StudentHome = () => <div className="p-10 text-2xl">🚧 学生端开发中...</div>;
const TeacherDashboard = () => <div className="p-10 text-2xl">🚧 教师端开发中...</div>;

function App() {
    return (
        // 2. 修改这里：使用 HashRouter 包裹
        <HashRouter>
            <Routes>
                <Route path="/" element={<Login />} />
                <Route path="/student" element={<StudentHome />} />
                <Route path="/teacher" element={<TeacherDashboard />} />
            </Routes>
        </HashRouter>
    );
}

export default App;