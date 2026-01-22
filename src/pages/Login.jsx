// 文件路径: src/pages/Login.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { GraduationCap, School, ChevronRight, BookOpen } from 'lucide-react';

const Login = () => {
    const navigate = useNavigate();

    return (
        // 全屏背景容器：使用德语国旗色调或同济蓝的渐变
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex flex-col items-center justify-center p-4">

            {/* 顶部标题区 */}
            <div className="text-center mb-10 space-y-2">
                <div className="flex items-center justify-center gap-2 text-blue-800 mb-2">
                    <School size={28} />
                    <span className="font-bold tracking-widest text-sm uppercase">Tongji University</span>
                </div>
                <h1 className="text-4xl md:text-5xl font-extrabold text-gray-900 tracking-tight">
                    AI 智能体德语助教
                </h1>
                <p className="text-gray-500 text-lg font-medium">
                    个性化学习路径探究系统
                </p>
            </div>

            {/* 核心卡片容器 */}
            <div className="bg-white/80 backdrop-blur-lg rounded-2xl shadow-xl w-full max-w-md p-8 border border-white/50">
                <h2 className="text-xl font-semibold text-gray-800 mb-6 flex items-center gap-2">
                    <BookOpen className="text-blue-600" size={20} />
                    请选择您的身份 / Bitte wählen
                </h2>

                <div className="space-y-4">
                    {/* 学生入口按钮 */}
                    <button
                        onClick={() => navigate('/student')}
                        className="group w-full relative overflow-hidden bg-white border-2 border-blue-100 hover:border-blue-500 rounded-xl p-4 transition-all duration-300 text-left hover:shadow-lg"
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="bg-blue-100 p-3 rounded-lg group-hover:bg-blue-600 transition-colors duration-300">
                                    <GraduationCap className="text-blue-600 group-hover:text-white" size={24} />
                                </div>
                                <div>
                                    <h3 className="font-bold text-gray-800">我是学生</h3>
                                    <p className="text-sm text-gray-500">Student / Schüler</p>
                                </div>
                            </div>
                            <ChevronRight className="text-gray-300 group-hover:text-blue-600 transform group-hover:translate-x-1 transition-all" />
                        </div>
                    </button>

                    {/* 教师入口按钮 */}
                    <button
                        onClick={() => navigate('/teacher')}
                        className="group w-full relative overflow-hidden bg-white border-2 border-indigo-100 hover:border-indigo-500 rounded-xl p-4 transition-all duration-300 text-left hover:shadow-lg"
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="bg-indigo-100 p-3 rounded-lg group-hover:bg-indigo-600 transition-colors duration-300">
                                    <School className="text-indigo-600 group-hover:text-white" size={24} />
                                </div>
                                <div>
                                    <h3 className="font-bold text-gray-800">我是教师</h3>
                                    <p className="text-sm text-gray-500">Lehrer / Dozent</p>
                                </div>
                            </div>
                            <ChevronRight className="text-gray-300 group-hover:text-indigo-600 transform group-hover:translate-x-1 transition-all" />
                        </div>
                    </button>
                </div>

                {/* 底部信息 */}
                <div className="mt-8 pt-6 border-t border-gray-100 text-center">
                    <p className="text-xs text-gray-400">
                        SITP 项目编号: 20251213 | 指导教师: 汤春艳
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Login;