import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import request from '../../api/request';
import { API_STUDENT_LOGIN } from '../../api/config';
import { GraduationCap, Lock, User, ArrowLeft, Eye, EyeOff, ShieldCheck, AlertCircle, RefreshCw, UserPlus } from 'lucide-react';

// 浮动粒子数据（与首页统一设计语言）
const PARTICLES = [
    { text: 'Ä', left: '8%', duration: 20, delay: 0, size: '1.1rem' },
    { text: 'Hallo', left: '18%', duration: 24, delay: 4, size: '0.85rem' },
    { text: 'ß', left: '30%', duration: 19, delay: 7, size: '1.2rem' },
    { text: 'Ö', left: '70%', duration: 22, delay: 2, size: '1rem' },
    { text: 'Deutsch', left: '82%', duration: 26, delay: 6, size: '0.8rem' },
    { text: 'Buch', left: '92%', duration: 23, delay: 10, size: '0.9rem' },
];

const StudentLogin = () => {
    const navigate = useNavigate();
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // 🔐 验证码与锁定状态
    const [showCaptcha, setShowCaptcha] = useState(() => localStorage.getItem('captcha_student') === 'true');
    const [captcha, setCaptcha] = useState({ code: '', dataUrl: '' });

    // 🚦 登录限制状态
    const [failedAttempts, setFailedAttempts] = useState(() => parseInt(localStorage.getItem('failed_attempts_student') || '0', 10));
    const [lockoutUntil, setLockoutUntil] = useState(() => parseInt(localStorage.getItem('lockout_until_student') || '0', 10));
    const [lockoutRemaining, setLockoutRemaining] = useState(0);

    const [formData, setFormData] = useState({
        studentId: '',
        password: '',
        captchaInput: ''
    });

    // 🎨 图形验证码生成逻辑
    const refreshCaptcha = () => {
        const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
        let code = '';
        for (let i = 0; i < 4; i++) {
            code += chars.charAt(Math.floor(Math.random() * chars.length));
        }

        const canvas = document.createElement('canvas');
        canvas.width = 120;
        canvas.height = 40;
        const ctx = canvas.getContext('2d');

        ctx.fillStyle = 'rgba(30, 30, 60, 0.8)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        for (let i = 0; i < 7; i++) {
            ctx.strokeStyle = `rgba(255, 255, 255, ${Math.random() * 0.1})`;
            ctx.beginPath();
            ctx.moveTo(Math.random() * canvas.width, Math.random() * canvas.height);
            ctx.lineTo(Math.random() * canvas.width, Math.random() * canvas.height);
            ctx.stroke();
        }

        ctx.font = 'bold 24px Inter, sans-serif';
        ctx.textBaseline = 'middle';
        const startX = 20;
        for (let i = 0; i < 4; i++) {
            const char = code[i];
            ctx.save();
            const x = startX + i * 25;
            const y = canvas.height / 2 + (Math.random() - 0.5) * 10;
            const angle = (Math.random() - 0.5) * 0.5;

            ctx.translate(x, y);
            ctx.rotate(angle);
            ctx.fillStyle = `hsl(${200 + Math.random() * 60}, 80%, 70%)`;
            ctx.fillText(char, 0, 0);
            ctx.restore();
        }

        setCaptcha({ code: code, dataUrl: canvas.toDataURL() });
    };

    useEffect(() => {
        refreshCaptcha();
    }, []);

    // 倒计时逻辑
    useEffect(() => {
        let timer;
        if (lockoutUntil > 0) {
            const updateTimer = () => {
                const now = Date.now();
                if (now >= lockoutUntil) {
                    setLockoutUntil(0);
                    setFailedAttempts(0);
                    setLockoutRemaining(0);
                    localStorage.removeItem('lockout_until_student');
                    localStorage.removeItem('failed_attempts_student');
                } else {
                    setLockoutRemaining(Math.ceil((lockoutUntil - now) / 1000));
                }
            };

            updateTimer(); // Initial call
            timer = setInterval(updateTimer, 1000);
        }
        return () => clearInterval(timer);
    }, [lockoutUntil]);

    const formatTime = (seconds) => {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m > 0 ? m + '分' : ''}${s}秒`;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (lockoutUntil > Date.now()) {
            setError(`由于多次尝试失败，账号已锁定。请在 ${formatTime(lockoutRemaining)} 后重试`);
            return;
        }

        setLoading(true);
        setError('');

        if (showCaptcha && formData.captchaInput.toUpperCase() !== captcha.code) {
            setError('验证码错误，请重新输入');
            setLoading(false);
            refreshCaptcha();
            setFormData(prev => ({ ...prev, captchaInput: '' }));
            return;
        }

        try {
            const response = await request.post(API_STUDENT_LOGIN, {
                username: formData.studentId,
                password: formData.password
            });

            if (response.data.code !== 200) {
                throw new Error(response.data.message || '登录失败');
            }

            let token = response.data.token || response.data.data?.token;
            let mockUser = response.data.user || response.data.data?.user;

            if (!token) {
                throw new Error("登录成功，但未找到登录凭证");
            }

            const displayUser = {
                ...mockUser,
                id: formData.studentId,
                name: mockUser.name,
                role: 'student'
            };

            localStorage.setItem('authToken', token);
            localStorage.setItem('userInfo', JSON.stringify(displayUser));
            localStorage.removeItem('captcha_student');
            localStorage.removeItem('failed_attempts_student');
            localStorage.removeItem('lockout_until_student');

            navigate(`/student/${displayUser.id}/home`);

        } catch (err) {
            console.error('🔴 学生登录错误:', err);

            const newAttempts = failedAttempts + 1;
            setFailedAttempts(newAttempts);
            localStorage.setItem('failed_attempts_student', newAttempts.toString());

            if (newAttempts >= 5) {
                const unlockTime = Date.now() + 2 * 60 * 1000; // 2 minutes
                setLockoutUntil(unlockTime);
                localStorage.setItem('lockout_until_student', unlockTime.toString());
                setError(`密码错误次数过多，请在 2分钟 后重试`);
            } else {
                setShowCaptcha(true);
                localStorage.setItem('captcha_student', 'true');
                refreshCaptcha();

                if (err.response) {
                    setError(`登录失败: ${err.response.data.message || '账号或密码错误'} (剩余尝试次数: ${5 - newAttempts})`);
                } else if (err.request) {
                    setError('无法连接服务器 (网络/跨域错误)');
                } else {
                    setError(err.message || '未知错误');
                }
            }

            setFormData(prev => ({ ...prev, captchaInput: '' }));
        } finally {
            setLoading(false);
        }
    };

    const isLocked = lockoutRemaining > 0;

    return (
        <div className="min-h-screen theme-bg-premium flex flex-col items-center justify-center p-4 relative">
            {/* 光圈装饰 */}
            <div className="glow-orb glow-orb-1" />
            <div className="glow-orb glow-orb-2" />

            {/* 浮动粒子 */}
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

            {/* 返回首页 */}
            <div className="w-full max-w-md mb-6 relative z-10 animate-fade-in">
                <button
                    onClick={() => navigate('/')}
                    className="flex items-center text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors text-sm font-medium"
                >
                    <ArrowLeft size={16} className="mr-1" /> 返回首页
                </button>
            </div>

            {/* Logo + 标题 */}
            <div className="text-center mb-8 relative z-10 animate-fade-in-up">
                <div className="flex justify-center mb-4">
                    <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center shadow-lg shadow-blue-500/30 transform rotate-3">
                        <GraduationCap className="text-white h-8 w-8" />
                    </div>
                </div>
                <h2 className="text-3xl font-extrabold text-gray-800 dark:text-white">学生端登录</h2>
                <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">Student Login · Anmeldung</p>
            </div>

            {/* 登录表单卡片 */}
            <div className="w-full max-w-md relative z-10 animate-fade-in-up delay-200">
                <div className="theme-glass-card rounded-2xl py-8 px-6 sm:px-10">
                    {/* 错误提示 */}
                    {error && (
                        <div className="mb-5 bg-red-500/10 border border-red-500/30 p-4 rounded-xl flex items-start">
                            <AlertCircle className="h-5 w-5 text-red-400 mr-2 flex-shrink-0 mt-0.5" />
                            <p className="text-sm text-red-300">{error}</p>
                        </div>
                    )}

                    <form className="space-y-5" onSubmit={handleSubmit}>
                        {/* 学号输入框 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">学号 / Student ID</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                                    <User className="h-5 w-5 text-gray-400 dark:text-gray-500" />
                                </div>
                                <input
                                    id="input-student-id"
                                    type="text"
                                    required
                                    className="input-glow-blue block w-full pl-11 pr-3 py-3 bg-gray-50/50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl text-gray-800 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none sm:text-sm transition-all"
                                    placeholder="请输入学号"
                                    value={formData.studentId}
                                    onChange={(e) => setFormData({ ...formData, studentId: e.target.value })}
                                />
                            </div>
                        </div>

                        {/* 密码输入框 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">密码 / Passwort</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                                    <Lock className="h-5 w-5 text-gray-400 dark:text-gray-500" />
                                </div>
                                <input
                                    id="input-student-password"
                                    type={showPassword ? "text" : "password"}
                                    required
                                    className="input-glow-blue block w-full pl-11 pr-11 py-3 bg-gray-50/50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl text-gray-800 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none sm:text-sm transition-all"
                                    placeholder="请输入密码"
                                    value={formData.password}
                                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                />
                                <div className="absolute inset-y-0 right-0 pr-3.5 flex items-center">
                                    <button type="button" onClick={() => setShowPassword(!showPassword)} className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors">
                                        {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* 验证码区域 */}
                        {showCaptcha && (
                            <div className="animate-fade-in-up">
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">验证码 / Captcha</label>
                                <div className="flex gap-3">
                                    <div className="relative flex-1">
                                        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                                            <ShieldCheck className="h-5 w-5 text-gray-400 dark:text-gray-500" />
                                        </div>
                                        <input
                                            id="input-student-captcha"
                                            type="text"
                                            required={showCaptcha}
                                            maxLength={4}
                                            className="input-glow-blue block w-full pl-11 pr-3 py-3 bg-gray-50/50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl text-gray-800 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none sm:text-sm tracking-widest uppercase transition-all"
                                            placeholder="验证码"
                                            value={formData.captchaInput}
                                            onChange={(e) => setFormData({ ...formData, captchaInput: e.target.value })}
                                        />
                                    </div>
                                    <div className="relative group cursor-pointer" onClick={refreshCaptcha}>
                                        <img
                                            src={captcha.dataUrl || null}
                                            alt="Captcha"
                                            className="h-[46px] w-[120px] rounded-xl border border-gray-200 dark:border-white/10 object-cover"
                                        />
                                        <div className="absolute inset-0 bg-black/20 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                            <RefreshCw className="text-white drop-shadow-md" size={20} />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* 登录按钮 */}
                        <button
                            id="btn-student-login"
                            type="submit"
                            disabled={loading || isLocked}
                            className={`w-full flex justify-center py-3.5 px-4 rounded-xl text-sm font-semibold text-white ${isLocked ? 'bg-gray-400 dark:bg-gray-600 cursor-not-allowed' : 'btn-gradient-blue focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 focus:ring-offset-gray-900'} ${loading ? 'opacity-70 cursor-not-allowed' : ''} transition-all duration-300`}
                        >
                            {isLocked ? (
                                <span className="flex items-center"><Lock className="mr-2 h-5 w-5" /> 锁定中 ({formatTime(lockoutRemaining)})</span>
                            ) : loading ? '登录中...' : <span className="flex items-center"><ShieldCheck className="mr-2 h-5 w-5" /> 登录 / Anmelden</span>}
                        </button>
                    </form>

                    {/* 注册入口 */}
                    <div className="mt-6 pt-5 border-t border-gray-200 dark:border-white/10 text-center">
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            没有账号？
                            <button
                                id="link-student-register"
                                onClick={() => navigate('/student/register')}
                                className="ml-1 text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 font-semibold transition-colors inline-flex items-center gap-1"
                            >
                                <UserPlus size={14} />
                                立即注册
                            </button>
                        </p>
                    </div>

                    <div className="mt-4 text-center text-xs text-gray-400 dark:text-gray-600">
                        点击图片可刷新验证码
                    </div>
                </div>
            </div>
        </div>
    );
};

export default StudentLogin;