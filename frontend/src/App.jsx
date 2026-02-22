import React from 'react';
import {HashRouter, Routes, Route, Navigate} from 'react-router-dom';
import Login from './pages/Login';
import StudentHome from './pages/student/StudentHome';
import TeacherLogin from './pages/teacher/TeacherLogin';
import TeacherDashboard from './pages/teacher/TeacherDashboard';
import ScenarioLaunch from './pages/teacher/ScenarioLaunch';
import ExamGenerator from './pages/teacher/ExamGenerator';
import StudentDetail from './pages/teacher/StudentDetail';
import StudentLogin from './pages/student/StudentLogin';
import AISceneChat from './pages/student/AISceneChat';
import ErrorBookReview from './pages/student/ErrorBookReview';
import FavoritesPage from './pages/student/FavoritesPage';
import GrammarPractice from './pages/student/GrammarPractice';
import LearningProgress from './pages/student/LearningProgress';
import ListeningSpeaking from './pages/student/ListeningSpeaking';
import VocabLearning from './pages/student/VocabLearning';
import WritingAssistant from './pages/student/WritingAssistant';

// 文件路径: src/App.jsx

// 🔒 以下为教师端同学原有代码，完全未修改，100%原样保留
// 引入原有页面

// 引入新拆分的教师端功能页面
// 🔒 教师端原有代码结束，以上内容完全未动

// 🆕 新增：学生端所有功能页面导入（仅新增，不影响原有代码）

function App() {
    return (
        <HashRouter>
            <Routes>
                {/* 1. 首页（原有代码，完全未修改） */}
                <Route path="/" element={<Login/>}/>

                {/* 🆕 新增：学生端完整路由配置（仅新增，不碰教师端代码） */}
                {/* 学生端根路径自动跳转到登录页，符合你的登录流程 */}
                <Route path="/student" element={<Navigate to="/student/login" replace/>}/>
                {/* 学生登录页 */}
                <Route path="/student/login" element={<StudentLogin/>}/>
                {/* 学生主页（登录成功后跳转） */}
                <Route path="/student/home" element={<StudentHome/>}/>
                {/* 学生端所有功能页面路由 */}
                <Route path="/student/ai-scene-chat" element={<AISceneChat/>}/>
                <Route path="/student/error-book" element={<ErrorBookReview/>}/>
                <Route path="/student/favorites" element={<FavoritesPage/>}/>
                <Route path="/student/grammar-practice" element={<GrammarPractice/>}/>
                <Route path="/student/learning-progress" element={<LearningProgress/>}/>
                <Route path="/student/listening-speaking" element={<ListeningSpeaking/>}/>
                <Route path="/student/vocab-learning" element={<VocabLearning/>}/>
                <Route path="/student/writing-assistant" element={<WritingAssistant/>}/>

                {/* 🔒 以下为教师端同学原有代码，完全未修改，100%原样保留 */}
                {/* 3. 教师端核心流程 */}
                <Route path="/teacher/login" element={<TeacherLogin/>}/>
                <Route path="/teacher/dashboard" element={<TeacherDashboard/>}/>

                {/* 4. 教师端子功能页面 */}
                <Route path="/teacher/scenario" element={<ScenarioLaunch/>}/>
                <Route path="/teacher/exam" element={<ExamGenerator/>}/>
                <Route path="/teacher/student/:id" element={<StudentDetail/>}/>
                {/* 🔒 教师端原有代码结束，以上内容完全未动 */}
            </Routes>
        </HashRouter>
    );
}

export default App;