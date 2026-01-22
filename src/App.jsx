// 文件路径: src/App.jsx
import React from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';

// 引入原有页面
import Login from './pages/Login';
import StudentHome from './pages/student/StudentHome';
import TeacherLogin from './pages/teacher/TeacherLogin';
import TeacherDashboard from './pages/teacher/TeacherDashboard';

// 引入新拆分的教师端功能页面
import ScenarioLaunch from './pages/teacher/ScenarioLaunch';
import ExamGenerator from './pages/teacher/ExamGenerator';
import StudentDetail from './pages/teacher/StudentDetail';

function App() {
    return (
        <HashRouter>
            <Routes>
                {/* 1. 首页 */}
                <Route path="/" element={<Login />} />

                {/* 2. 学生端 */}
                <Route path="/student" element={<StudentHome />} />

                {/* 3. 教师端核心流程 */}
                <Route path="/teacher/login" element={<TeacherLogin />} />
                <Route path="/teacher/dashboard" element={<TeacherDashboard />} />

                {/* 4. 教师端子功能页面 */}
                <Route path="/teacher/scenario" element={<ScenarioLaunch />} />
                <Route path="/teacher/exam" element={<ExamGenerator />} />
                <Route path="/teacher/student/:id" element={<StudentDetail />} />
            </Routes>
        </HashRouter>
    );
}

export default App;