import React from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import StudentHome from './pages/student/StudentHome';
import TeacherLogin from './pages/teacher/TeacherLogin';
import TeacherDashboard from './pages/teacher/TeacherDashboard';
import ScenarioLaunch from './pages/teacher/ScenarioLaunch';
import ExamGenerator from './pages/teacher/ExamGenerator';
import StudentDetail from './pages/teacher/StudentDetail';
import TeacherHistory from './pages/teacher/TeacherHistory';
import TeacherAI from './pages/teacher/TeacherAI';
import StudentLogin from './pages/student/StudentLogin';
import AISceneChat from './pages/student/AISceneChat';
import ErrorBookReview from './pages/student/ErrorBookReview';
import FavoritesPage from './pages/student/FavoritesPage';
import GrammarPractice from './pages/student/GrammarPractice';
import LearningProgress from './pages/student/LearningProgress';
import ListeningSpeaking from './pages/student/ListeningSpeaking';
import VocabLearning from './pages/student/VocabLearning';
import WritingAssistant from './pages/student/WritingAssistant';
import ProtectedRoute from './components/ProtectedRoute';

// 文件路径: src/App.jsx

function App() {
    return (
        <HashRouter>
            <Routes>
                {/* 1. 首页（身份选择） */}
                <Route path="/" element={<Login />} />

                {/* ── 学生端路由 ── */}
                <Route path="/student" element={<Navigate to="/student/login" replace />} />
                <Route path="/student/login" element={<StudentLogin />} />
                {/* 以下学生端页面需要登录 + 学生角色，并带有唯一 userId */}
                <Route path="/student/:userId/home" element={<ProtectedRoute requiredRole="student"><StudentHome /></ProtectedRoute>} />
                <Route path="/student/:userId/ai-scene-chat" element={<ProtectedRoute requiredRole="student"><AISceneChat /></ProtectedRoute>} />
                <Route path="/student/:userId/error-book" element={<ProtectedRoute requiredRole="student"><ErrorBookReview /></ProtectedRoute>} />
                <Route path="/student/:userId/favorites" element={<ProtectedRoute requiredRole="student"><FavoritesPage /></ProtectedRoute>} />
                <Route path="/student/:userId/grammar-practice" element={<ProtectedRoute requiredRole="student"><GrammarPractice /></ProtectedRoute>} />
                <Route path="/student/:userId/learning-progress" element={<ProtectedRoute requiredRole="student"><LearningProgress /></ProtectedRoute>} />
                <Route path="/student/:userId/listening-speaking" element={<ProtectedRoute requiredRole="student"><ListeningSpeaking /></ProtectedRoute>} />
                <Route path="/student/:userId/vocab-learning" element={<ProtectedRoute requiredRole="student"><VocabLearning /></ProtectedRoute>} />
                <Route path="/student/:userId/writing-assistant" element={<ProtectedRoute requiredRole="student"><WritingAssistant /></ProtectedRoute>} />

                {/* ── 教师端路由 ── */}
                <Route path="/teacher/login" element={<TeacherLogin />} />
                {/* 以下教师端页面需要登录 + 教师角色 */}
                <Route path="/teacher/dashboard" element={<ProtectedRoute requiredRole="teacher"><TeacherDashboard /></ProtectedRoute>} />
                <Route path="/teacher/scenario" element={<ProtectedRoute requiredRole="teacher"><ScenarioLaunch /></ProtectedRoute>} />
                <Route path="/teacher/exam" element={<ProtectedRoute requiredRole="teacher"><ExamGenerator /></ProtectedRoute>} />
                <Route path="/teacher/history" element={<ProtectedRoute requiredRole="teacher"><TeacherHistory /></ProtectedRoute>} />
                <Route path="/teacher/ai" element={<ProtectedRoute requiredRole="teacher"><TeacherAI /></ProtectedRoute>} />
                <Route path="/teacher/student/:id" element={<ProtectedRoute requiredRole="teacher"><StudentDetail /></ProtectedRoute>} />
            </Routes>
        </HashRouter>
    );
}

export default App;