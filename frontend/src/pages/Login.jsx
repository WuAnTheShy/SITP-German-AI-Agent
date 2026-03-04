// 文件路径: src/pages/Login.jsx
import React, { useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { GraduationCap, School, ChevronRight, BookOpen, Sparkles } from 'lucide-react';

// 德语字母/单词粒子数据
const PARTICLES = [
    { text: 'Ä', left: '5%', duration: 18, delay: 0, size: '1.2rem' },
    { text: 'Ö', left: '15%', duration: 22, delay: 3, size: '1rem' },
    { text: 'Ü', left: '25%', duration: 20, delay: 7, size: '1.4rem' },
    { text: 'ß', left: '35%', duration: 24, delay: 1, size: '1.1rem' },
    { text: 'Hallo', left: '45%', duration: 26, delay: 5, size: '0.9rem' },
    { text: 'Danke', left: '55%', duration: 19, delay: 9, size: '0.85rem' },
    { text: 'Guten Tag', left: '65%', duration: 23, delay: 2, size: '0.8rem' },
    { text: 'Deutsch', left: '75%', duration: 21, delay: 6, size: '0.95rem' },
    { text: 'Lernen', left: '85%', duration: 25, delay: 4, size: '0.9rem' },
    { text: 'Schule', left: '92%', duration: 20, delay: 8, size: '0.85rem' },
    { text: 'Buch', left: '10%', duration: 27, delay: 11, size: '1rem' },
    { text: 'Wort', left: '50%', duration: 22, delay: 13, size: '0.9rem' },
];

const Login = () => {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen theme-bg-premium flex flex-col items-center justify-center p-4 relative">
            {/* 渐变光圈装饰 */}
            <div className="glow-orb glow-orb-1" />
            <div className="glow-orb glow-orb-2" />
            <div className="glow-orb glow-orb-3" />

            {/* 浮动德语字母粒子 */}
            {PARTICLES.map((p, i) => (
                <span
                    key={i}
                    className="floating-particle"
                    style={{
                        left: p.left,
                        fontSize: p.size,
                        animationDuration: `${p.duration}s`,
                        animationDelay: `${p.delay}s`,
                    }}
                >
                    {p.text}
                </span>
            ))}

            {/* 顶部标题区 */}
            <div className="text-center mb-10 space-y-3 relative z-10 animate-fade-in-up">
                <div className="flex items-center justify-center gap-2 mb-3">
                    <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center">
                        <School size={16} className="text-white" />
                    </div>
                    <span className="font-semibold tracking-[0.2em] text-xs uppercase text-blue-300/80">
                        Tongji University
                    </span>
                </div>
                <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight">
                    <span className="shimmer-text">AI 智能体德语助教</span>
                </h1>
                <p className="text-gray-400 text-lg font-medium tracking-wide">
                    个性化学习路径探究系统 · Personalisiertes Lernsystem
                </p>
            </div>

            {/* 核心卡片容器 */}
            <div className="theme-glass-card rounded-2xl w-full max-w-md p-8 relative z-10 animate-fade-in-up delay-200">
                <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-6 flex items-center gap-2">
                    <Sparkles className="text-blue-400" size={18} />
                    请选择您的身份 / Bitte wählen
                </h2>

                <div className="space-y-4">
                    {/* 学生入口按钮 */}
                    <button
                        id="btn-student-entry"
                        onClick={() => navigate('/student/login')}
                        className="group w-full bg-white/40 dark:bg-white/5 border border-white/40 dark:border-white/10 rounded-xl p-5 transition-all duration-300 text-left hover:bg-white/60 dark:hover:bg-white/10 hover:border-blue-400/30 hover:shadow-lg hover:shadow-blue-500/10"
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="bg-blue-500/10 dark:bg-blue-500/20 p-3 rounded-xl group-hover:bg-blue-500/20 dark:group-hover:bg-blue-500/30 transition-all duration-300 group-hover:scale-105">
                                    <GraduationCap className="text-blue-500 dark:text-blue-400 group-hover:text-blue-600 dark:group-hover:text-blue-300" size={24} />
                                </div>
                                <div>
                                    <h3 className="font-bold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-200 transition-colors">
                                        我是学生
                                    </h3>
                                    <p className="text-sm text-gray-500 dark:text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300 transition-colors">
                                        Student · Schüler
                                    </p>
                                </div>
                            </div>
                            <ChevronRight className="text-gray-500 group-hover:text-blue-400 transform group-hover:translate-x-1 transition-all" />
                        </div>
                    </button>

                    {/* 教师入口按钮 */}
                    <button
                        id="btn-teacher-entry"
                        onClick={() => navigate('/teacher/login')}
                        className="group w-full bg-white/40 dark:bg-white/5 border border-white/40 dark:border-white/10 rounded-xl p-5 transition-all duration-300 text-left hover:bg-white/60 dark:hover:bg-white/10 hover:border-indigo-400/30 hover:shadow-lg hover:shadow-indigo-500/10"
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="bg-indigo-500/10 dark:bg-indigo-500/20 p-3 rounded-xl group-hover:bg-indigo-500/20 dark:group-hover:bg-indigo-500/30 transition-all duration-300 group-hover:scale-105">
                                    <School className="text-indigo-500 dark:text-indigo-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-300" size={24} />
                                </div>
                                <div>
                                    <h3 className="font-bold text-gray-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-200 transition-colors">
                                        我是教师
                                    </h3>
                                    <p className="text-sm text-gray-500 dark:text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300 transition-colors">
                                        Lehrer · Dozent
                                    </p>
                                </div>
                            </div>
                            <ChevronRight className="text-gray-500 group-hover:text-indigo-400 transform group-hover:translate-x-1 transition-all" />
                        </div>
                    </button>
                </div>

                {/* 底部信息 */}
                <div className="mt-8 pt-6 border-t border-gray-200 dark:border-white/10 text-center">
                    <p className="text-xs text-gray-400 dark:text-gray-500">
                        SITP 项目编号: 20251213 | 指导教师: 汤春艳
                    </p>
                    <p className="text-xs text-gray-400 dark:text-gray-600 mt-1">
                        © 2026 Tongji University · Alle Rechte vorbehalten
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Login;