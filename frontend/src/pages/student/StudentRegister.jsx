import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import request from '../../api/request';
import { API_STUDENT_REGISTER } from '../../api/config';
import { GraduationCap, Lock, User, ArrowLeft, Eye, EyeOff, ShieldCheck, AlertCircle, RefreshCw, UserPlus, CheckCircle, BookOpen } from 'lucide-react';

const PARTICLES = [
    { text: 'Willkommen', left: '5%', duration: 22, delay: 0, size: '0.8rem' },
    { text: 'Ü', left: '25%', duration: 20, delay: 4, size: '1.2rem' },
    { text: 'Lernen', left: '50%', duration: 24, delay: 8, size: '0.85rem' },
    { text: 'ß', left: '75%', duration: 19, delay: 2, size: '1.3rem' },
    { text: 'Anfang', left: '90%', duration: 23, delay: 6, size: '0.9rem' },
];

const StudentRegister = () => {
    const navigate = useNavigate();
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirm, setShowConfirm] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const [captcha, setCaptcha] = useState({ code: '', dataUrl: '' });

    const [formData, setFormData] = useState({
        studentId: '',
        displayName: '',
        password: '',
        confirmPassword: '',
        captchaInput: ''
    });

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

        setCaptcha({ code, dataUrl: canvas.toDataURL() });
    };

    useEffect(() => {
        refreshCaptcha();
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        // 前端验证
        if (formData.password.length < 6) {
            setError('密码长度不能少于6位');
            setLoading(false);
            return;
        }

        if (formData.password !== formData.confirmPassword) {
            setError('两次输入的密码不一致');
            setLoading(false);
            return;
        }

        if (formData.captchaInput.toUpperCase() !== captcha.code) {
            setError('验证码错误，请重新输入');
            setLoading(false);
            refreshCaptcha();
            setFormData(prev => ({ ...prev, captchaInput: '' }));
            return;
        }

        try {
            const response = await request.post(API_STUDENT_REGISTER, {
                username: formData.studentId,
                password: formData.password,
                display_name: formData.displayName,
            });

            if (response.data.code !== 200) {
                throw new Error(response.data.message || '注册失败');
            }

            setSuccess(true);
            setTimeout(() => {
                navigate('/student/login');
            }, 2000);

        } catch (err) {
            console.error('🔴 学生注册错误:', err);
            refreshCaptcha();
            setFormData(prev => ({ ...prev, captchaInput: '' }));

            if (err.response) {
                setError(`注册失败: ${err.response.data?.message || err.response.data?.detail || '服务器错误'}`);
            } else if (err.request) {
                setError('无法连接服务器 (网络/跨域错误)');
            } else {
                setError(err.message || '未知错误');
            }
        } finally {
            setLoading(false);
        }
    };

    // 注册成功界面
    if (success) {
        return (
            <div className="min-h-screen theme-bg-premium flex flex-col items-center justify-center p-4 relative">
                <div className="glow-orb glow-orb-1" />
                <div className="glow-orb glow-orb-2" />
                <div className="theme-glass-card rounded-2xl p-10 text-center relative z-10 animate-fade-in-up max-w-md w-full">
                    <div className="h-20 w-20 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-6">
                        <CheckCircle className="text-green-500 dark:text-green-400 h-10 w-10" />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-2">注册成功！</h2>
                    <p className="text-gray-600 dark:text-gray-400 mb-1">Registrierung erfolgreich!</p>
                    <p className="text-gray-500 text-sm mt-4">正在跳转到登录页面...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen theme-bg-premium flex flex-col items-center justify-center p-4 relative">
            <div className="glow-orb glow-orb-1" />
            <div className="glow-orb glow-orb-2" />

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

            {/* 返回 */}
            <div className="w-full max-w-md mb-6 relative z-10 animate-fade-in">
                <button
                    onClick={() => navigate('/student/login')}
                    className="flex items-center text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors text-sm font-medium"
                >
                    <ArrowLeft size={16} className="mr-1" /> 返回登录
                </button>
            </div>

            {/* Logo + 标题 */}
            <div className="text-center mb-8 relative z-10 animate-fade-in-up">
                <div className="flex justify-center mb-4">
                    <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center shadow-lg shadow-blue-500/30 transform -rotate-3">
                        <UserPlus className="text-white h-8 w-8" />
                    </div>
                </div>
                <h2 className="text-3xl font-extrabold text-gray-800 dark:text-white">学生注册</h2>
                <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">Student Registration · Registrierung</p>
            </div>

            {/* 注册表单 */}
            <div className="w-full max-w-md relative z-10 animate-fade-in-up delay-200">
                <div className="theme-glass-card rounded-2xl py-8 px-6 sm:px-10">
                    {error && (
                        <div className="mb-5 bg-red-500/10 border border-red-500/30 p-4 rounded-xl flex items-start">
                            <AlertCircle className="h-5 w-5 text-red-400 mr-2 flex-shrink-0 mt-0.5" />
                            <p className="text-sm text-red-300">{error}</p>
                        </div>
                    )}

                    <form className="space-y-4" onSubmit={handleSubmit}>
                        {/* 学号 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">学号 / Student ID</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                                    <BookOpen className="h-5 w-5 text-gray-400 dark:text-gray-500" />
                                </div>
                                <input
                                    id="input-reg-student-id"
                                    type="text"
                                    required
                                    className="input-glow-blue block w-full pl-11 pr-3 py-3 bg-gray-50/50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl text-gray-800 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none sm:text-sm transition-all"
                                    placeholder="请输入学号"
                                    value={formData.studentId}
                                    onChange={(e) => setFormData({ ...formData, studentId: e.target.value })}
                                />
                            </div>
                        </div>

                        {/* 姓名 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">姓名 / Name</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                                    <User className="h-5 w-5 text-gray-400 dark:text-gray-500" />
                                </div>
                                <input
                                    id="input-reg-student-name"
                                    type="text"
                                    required
                                    className="input-glow-blue block w-full pl-11 pr-3 py-3 bg-gray-50/50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl text-gray-800 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none sm:text-sm transition-all"
                                    placeholder="请输入姓名"
                                    value={formData.displayName}
                                    onChange={(e) => setFormData({ ...formData, displayName: e.target.value })}
                                />
                            </div>
                        </div>

                        {/* 密码 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">密码 / Passwort</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                                    <Lock className="h-5 w-5 text-gray-400 dark:text-gray-500" />
                                </div>
                                <input
                                    id="input-reg-student-password"
                                    type={showPassword ? "text" : "password"}
                                    required
                                    className="input-glow-blue block w-full pl-11 pr-11 py-3 bg-gray-50/50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl text-gray-800 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none sm:text-sm transition-all"
                                    placeholder="至少6位密码"
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

                        {/* 确认密码 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">确认密码 / Bestätigen</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                                    <Lock className="h-5 w-5 text-gray-400 dark:text-gray-500" />
                                </div>
                                <input
                                    id="input-reg-student-confirm"
                                    type={showConfirm ? "text" : "password"}
                                    required
                                    className="input-glow-blue block w-full pl-11 pr-11 py-3 bg-gray-50/50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl text-gray-800 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none sm:text-sm transition-all"
                                    placeholder="再次输入密码"
                                    value={formData.confirmPassword}
                                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                                />
                                <div className="absolute inset-y-0 right-0 pr-3.5 flex items-center">
                                    <button type="button" onClick={() => setShowConfirm(!showConfirm)} className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors">
                                        {showConfirm ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* 验证码 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">验证码 / Captcha</label>
                            <div className="flex gap-3">
                                <div className="relative flex-1">
                                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                                        <ShieldCheck className="h-5 w-5 text-gray-400 dark:text-gray-500" />
                                    </div>
                                    <input
                                        id="input-reg-student-captcha"
                                        type="text"
                                        required
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

                        {/* 注册按钮 */}
                        <button
                            id="btn-student-register"
                            type="submit"
                            disabled={loading}
                            className={`w-full flex justify-center py-3.5 px-4 rounded-xl text-sm font-semibold text-white btn-gradient-blue focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 focus:ring-offset-gray-900 mt-2 ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
                        >
                            {loading ? '注册中...' : <span className="flex items-center"><UserPlus className="mr-2 h-5 w-5" /> 注册 / Registrieren</span>}
                        </button>
                    </form>

                    {/* 登录入口 */}
                    <div className="mt-6 pt-5 border-t border-gray-200 dark:border-white/10 text-center">
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            已有账号？
                            <button
                                onClick={() => navigate('/student/login')}
                                className="ml-1 text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 font-semibold transition-colors"
                            >
                                立即登录
                            </button>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default StudentRegister;
