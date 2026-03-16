// 文件路径: src/pages/Login.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { School, Lock, User, Eye, EyeOff, ShieldCheck, AlertCircle, RefreshCw, UserPlus, Sparkles } from 'lucide-react';
import request from '../api/request';
import { API_LOGIN, API_STUDENT_LOGIN } from '../api/config';

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
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // 🔐 验证码与锁定状态
    const [showCaptcha, setShowCaptcha] = useState(() => localStorage.getItem('captcha_unified') === 'true');
    const [captcha, setCaptcha] = useState({ code: '', dataUrl: '' });

    // 🚦 登录限制状态
    const [failedAttempts, setFailedAttempts] = useState(() => parseInt(localStorage.getItem('failed_attempts_unified') || '0', 10));
    const [lockoutUntil, setLockoutUntil] = useState(() => parseInt(localStorage.getItem('lockout_until_unified') || '0', 10));
    const [lockoutRemaining, setLockoutRemaining] = useState(0);

    const [formData, setFormData] = useState({
        username: '',
        password: '',
        captchaInput: ''
    });

    const isLocked = lockoutUntil > Date.now();

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

        ctx.fillStyle = 'rgba(30, 25, 55, 0.8)';
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
            ctx.fillStyle = `hsl(${220 + Math.random() * 40}, 80%, 70%)`;
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
                    localStorage.removeItem('lockout_until_unified');
                    localStorage.removeItem('failed_attempts_unified');
                } else {
                    setLockoutRemaining(Math.ceil((lockoutUntil - now) / 1000));
                }
            };

            updateTimer();
            timer = setInterval(updateTimer, 1000);
        }
        return () => clearInterval(timer);
    }, [lockoutUntil]);

    const formatTime = (seconds) => {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m > 0 ? m + '分' : ''}${s}秒`;
    };

    const attemptLogin = async (url, credentials) => {
        try {
            const response = await request.post(url, credentials);
            if (response.data.code === 200) return response.data;
            return null;
        } catch (err) {
            return null;
        }
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
            // 1. 尝试学生登录
            let loginData = await attemptLogin(API_STUDENT_LOGIN, {
                username: formData.username,
                password: formData.password
            });

            if (loginData) {
                // 学生登录成功
                handleLoginSuccess('student', loginData);
                return;
            }

            // 2. 尝试教工登录
            loginData = await attemptLogin(API_LOGIN, {
                username: formData.username,
                password: formData.password
            });

            if (loginData) {
                // 教工登录成功
                handleLoginSuccess('teacher', loginData);
                return;
            }

            // 3. 都失败了
            throw new Error('账号或密码错误');

        } catch (err) {
            handleLoginFailure(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleLoginSuccess = (role, data) => {
        const token = data.token || data.data?.token;
        const user = data.user || data.data?.user;

        if (role === 'student') {
            const displayUser = {
                ...user,
                id: formData.username,
                name: user?.name ?? formData.username,
                role: 'student'
            };
            localStorage.setItem('authToken', token);
            localStorage.setItem('userInfo', JSON.stringify(displayUser));
            clearLoginLimits();
            navigate(`/student/${displayUser.id}/home`);
        } else {
            const isAdminToken = typeof token === 'string' && token.startsWith('admin-token-');
            const isAdminAccount = (formData.username || '').trim().toLowerCase() === 'admin';
            const actualRole = (isAdminToken || (isAdminAccount && user)) ? 'admin' : (user?.role || 'teacher');
            
            const displayUser = {
                ...user,
                id: formData.username,
                name: user?.name ?? user?.display_name ?? (actualRole === 'admin' ? '管理员' : formData.username),
                role: actualRole
            };

            localStorage.setItem('authToken', token);
            localStorage.setItem('userInfo', JSON.stringify(displayUser));
            clearLoginLimits();

            if (displayUser.role === 'admin') {
                navigate('/admin/dashboard', { replace: true });
            } else {
                navigate(`/teacher/${formData.username}/dashboard`, { replace: true });
            }
        }
    };

    const handleLoginFailure = (message) => {
        const newAttempts = failedAttempts + 1;
        setFailedAttempts(newAttempts);
        localStorage.setItem('failed_attempts_unified', newAttempts.toString());

        if (newAttempts >= 5) {
            const unlockTime = Date.now() + 2 * 60 * 1000;
            setLockoutUntil(unlockTime);
            setLockoutRemaining(120);
            localStorage.setItem('lockout_until_unified', unlockTime.toString());
            setError('密码错误次数过多，请在 2分钟 后重试');
        } else {
            setShowCaptcha(true);
            localStorage.setItem('captcha_unified', 'true');
            refreshCaptcha();
            setError(`${message} (剩余尝试次数: ${5 - newAttempts})`);
        }
        setFormData(prev => ({ ...prev, captchaInput: '' }));
    };

    const clearLoginLimits = () => {
        localStorage.removeItem('captcha_unified');
        localStorage.removeItem('failed_attempts_unified');
        localStorage.removeItem('lockout_until_unified');
    };

    return (
        <div className="min-h-screen theme-bg-premium flex flex-col items-center justify-center p-4 relative overflow-hidden">
            {/* 渐变装饰 */}
            <div className="glow-orb glow-orb-1" />
            <div className="glow-orb glow-orb-2" />
            <div className="glow-orb glow-orb-3" />

            {/* 粒子背景 */}
            {PARTICLES.map((p, i) => (
                <span key={i} className="floating-particle" style={{ left: p.left, fontSize: p.size, animationDuration: `${p.duration}s`, animationDelay: `${p.delay}s` }}>
                    {p.text}
                </span>
            ))}

            <div className="text-center mb-8 space-y-3 relative z-10 animate-fade-in-up">
                <div className="flex items-center justify-center gap-2 mb-3">
                    <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center">
                        <School size={16} className="text-white" />
                    </div>
                    <span className="font-semibold tracking-[0.2em] text-xs uppercase text-blue-300/80">Tongji University</span>
                </div>
                <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-gray-900 dark:text-white">
                    <span className="shimmer-text">AI 智能体德语助教</span>
                </h1>
                <p className="text-gray-400 dark:text-gray-300 text-lg font-medium tracking-wide">Personalisiertes Lernsystem</p>
            </div>

            <div className="theme-glass-card rounded-2xl w-full max-w-md p-8 relative z-10 animate-fade-in-up delay-200 overflow-hidden">
                <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-6 flex items-center gap-2">
                    <Sparkles className="text-blue-400" size={18} />
                    系统登录 / Anmeldung
                </h2>

                {error && (
                    <div className="mb-5 bg-red-500/10 border border-red-500/30 p-4 rounded-xl flex items-start">
                        <AlertCircle className="h-5 w-5 text-red-500 dark:text-red-400 mr-2 flex-shrink-0 mt-0.5" />
                        <p className="text-sm text-red-600 dark:text-red-300">{error}</p>
                    </div>
                )}

                <form className="space-y-6" onSubmit={handleSubmit}>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">账号 / Konto (ID)</label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                                <User className="h-5 w-5 text-blue-400" />
                            </div>
                            <input
                                type="text"
                                required
                                className="block w-full pl-11 pr-3 py-3 bg-gray-50/50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl text-gray-800 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none sm:text-sm transition-all input-glow-blue"
                                placeholder="请输入学号、工号或 admin"
                                value={formData.username}
                                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">密码 / Passwort</label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                                <Lock className="h-5 w-5 text-indigo-400" />
                            </div>
                            <input
                                type={showPassword ? "text" : "password"}
                                required
                                className="block w-full pl-11 pr-11 py-3 bg-gray-50/50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl text-gray-800 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none sm:text-sm transition-all input-glow"
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

                    {showCaptcha && (
                        <div className="animate-fade-in-up">
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">验证码 / Captcha</label>
                            <div className="flex gap-3">
                                <div className="relative flex-1">
                                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                                        <ShieldCheck className="h-5 w-5 text-blue-400" />
                                    </div>
                                    <input
                                        type="text"
                                        required={showCaptcha}
                                        maxLength={4}
                                        className="block w-full pl-11 pr-3 py-3 bg-gray-50/50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl text-gray-800 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none sm:text-sm tracking-widest uppercase transition-all input-glow-blue"
                                        placeholder="验证码"
                                        value={formData.captchaInput}
                                        onChange={(e) => setFormData({ ...formData, captchaInput: e.target.value })}
                                    />
                                </div>
                                <div className="relative group cursor-pointer" onClick={refreshCaptcha}>
                                    <img src={captcha.dataUrl || null} alt="Captcha" className="h-[46px] w-[120px] rounded-xl border border-gray-200 dark:border-white/10 object-cover" />
                                    <div className="absolute inset-0 bg-black/20 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                        <RefreshCw className="text-white drop-shadow-md" size={20} />
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading || isLocked}
                        className={`w-full flex justify-center py-3.5 px-4 rounded-xl text-sm font-semibold text-white transition-all duration-300 ${isLocked ? 'bg-gray-400 dark:bg-gray-600 cursor-not-allowed' : 'btn-gradient-blue focus:ring-blue-500'} ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
                    >
                        {isLocked ? (
                            <span className="flex items-center"><Lock className="mr-2 h-5 w-5" /> 锁定中 ({formatTime(lockoutRemaining)})</span>
                        ) : loading ? '登录中...' : <span className="flex items-center"><ShieldCheck className="mr-2 h-5 w-5" /> 立即登录 / Anmelden</span>}
                    </button>
                </form>

                <div className="mt-8 pt-6 border-t border-gray-200 dark:border-white/10 text-center space-y-4">
                    <div className="flex justify-center gap-6">
                        <button onClick={() => navigate('/student/register')} className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-500 font-semibold flex items-center gap-1 transition-colors">
                            <UserPlus size={14} /> 学生注册
                        </button>
                        <button onClick={() => navigate('/teacher/register')} className="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 font-semibold flex items-center gap-1 transition-colors">
                            <UserPlus size={14} /> 教工注册
                        </button>
                    </div>
                </div>
            </div>

            <div className="mt-8 text-center animate-fade-in delay-500">
                <p className="text-xs text-gray-400 dark:text-gray-500">
                    SITP 项目编号: 20251213 | © 2026 Tongji University
                </p>
            </div>
        </div>
    );
};

export default Login;