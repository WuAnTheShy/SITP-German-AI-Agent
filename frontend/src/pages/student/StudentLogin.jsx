import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { GraduationCap, Lock, User, ArrowLeft, Eye, EyeOff, ShieldCheck, AlertCircle, RefreshCw } from 'lucide-react';

// ----------------------------------------------------------------------
// 🔧 接口配置（和教师端同域名，后端同学直接对接，不用改）
// ----------------------------------------------------------------------
const MOCK_SERVER_BASE = 'https://m1.apifoxmock.com/m1/7746497-7491372-default';
const API_STUDENT_LOGIN_URL = `${MOCK_SERVER_BASE}/api/auth/student-login`;
// ----------------------------------------------------------------------

const StudentLogin = () => {
    const navigate = useNavigate();
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // 🔐 验证码状态（和教师端逻辑完全一致，保持项目统一）
    const [captcha, setCaptcha] = useState({ code: '', dataUrl: '' });

    // 表单数据（学生端用学号studentId，和教师端工号区分）
    const [formData, setFormData] = useState({
        studentId: '',
        password: '',
        captchaInput: ''
    });

    // 🎨 图形验证码生成逻辑（和教师端完全一致，不用改）
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

        // 绘制背景
        ctx.fillStyle = '#F3F4F6';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // 绘制干扰线
        for (let i = 0; i < 7; i++) {
            ctx.strokeStyle = `rgba(0, 0, 0, ${Math.random() * 0.2})`;
            ctx.beginPath();
            ctx.moveTo(Math.random() * canvas.width, Math.random() * canvas.height);
            ctx.lineTo(Math.random() * canvas.width, Math.random() * canvas.height);
            ctx.stroke();
        }

        // 绘制文字
        ctx.font = 'bold 24px sans-serif';
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
            ctx.fillStyle = `hsl(${Math.random() * 360}, 60%, 40%)`;
            ctx.fillText(char, 0, 0);
            ctx.restore();
        }

        setCaptcha({ code: code, dataUrl: canvas.toDataURL() });
    };

    // 页面加载时自动生成验证码
    useEffect(() => {
        refreshCaptcha();
    }, []);

    // 登录提交逻辑（接口已写死，不用后续再加）
    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        // 先校验验证码
        if (formData.captchaInput.toUpperCase() !== captcha.code) {
            setError('验证码错误，请重新输入');
            setLoading(false);
            refreshCaptcha();
            setFormData(prev => ({ ...prev, captchaInput: '' }));
            return;
        }

        try {
            console.log("🔵 [学生登录调试] 请求地址:", API_STUDENT_LOGIN_URL);

            // 发送登录请求（参数和教师端统一，后端好对接）
            const response = await axios.post(API_STUDENT_LOGIN_URL, {
                username: formData.studentId,
                password: formData.password
            });

            console.log("🟢 [学生登录调试] 服务器返回:", response.data);

            // 提取token和用户信息（和教师端逻辑统一）
            let token = response.data.token || response.data.data?.token;
            let mockUser = response.data.user || response.data.data?.user;

            if (!token) {
                throw new Error("登录成功，但未找到登录凭证");
            }

            // 构造学生用户信息，存入本地存储
            const displayUser = {
                ...mockUser,
                id: formData.studentId,
                name: mockUser.name,
                role: 'student'
            };

            localStorage.setItem('authToken', token);
            localStorage.setItem('userInfo', JSON.stringify(displayUser));

            // 登录成功，跳转到学生主页（和你的StudentHome.jsx对应）
            navigate('/student/home');

        } catch (err) {
            console.error('🔴 学生登录错误:', err);
            // 登录失败刷新验证码
            refreshCaptcha();
            setFormData(prev => ({ ...prev, captchaInput: '' }));

            // 错误提示
            if (err.response) {
                setError(`登录失败: ${err.response.data.message || '账号或密码错误'}`);
            } else if (err.request) {
                setError('无法连接服务器 (网络/跨域错误)');
            } else {
                setError(err.message || '未知错误');
            }
        } finally {
            setLoading(false);
        }
    };

    // 页面渲染（和教师端风格完全统一，只改了学生端相关文案）
    return (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
            <div className="sm:mx-auto sm:w-full sm:max-w-md mb-6 px-4">
                <button
                    onClick={() => navigate('/')}
                    className="flex items-center text-gray-500 hover:text-blue-600 transition-colors text-sm font-medium"
                >
                    <ArrowLeft size={16} className="mr-1"/> 返回首页
                </button>
            </div>

            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <div className="flex justify-center">
                    <div className="h-16 w-16 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg transform rotate-3">
                        <GraduationCap className="text-white h-8 w-8"/>
                    </div>
                </div>
                <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">学生端登录</h2>
            </div>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                <div className="bg-white py-8 px-4 shadow-xl sm:rounded-lg sm:px-10 border border-gray-100">
                    {/* 错误提示 */}
                    {error && (
                        <div className="mb-4 bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg flex items-start">
                            <AlertCircle className="h-5 w-5 text-red-500 mr-2 flex-shrink-0 mt-0.5"/>
                            <p className="text-sm text-red-700">{error}</p >
                        </div>
                    )}

                    <form className="space-y-6" onSubmit={handleSubmit}>
                        {/* 学号输入框 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700">学号 / Student ID</label>
                            <div className="mt-1 relative rounded-md shadow-sm">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <User className="h-5 w-5 text-gray-400"/>
                                </div>
                                <input
                                    type="text"
                                    required
                                    className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                    placeholder="请输入学号"
                                    value={formData.studentId}
                                    onChange={(e) => setFormData({...formData, studentId: e.target.value})}
                                />
                            </div>
                        </div>

                        {/* 密码输入框 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700">密码 / Password</label>
                            <div className="mt-1 relative rounded-md shadow-sm">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Lock className="h-5 w-5 text-gray-400"/>
                                </div>
                                <input
                                    type={showPassword ? "text" : "password"}
                                    required
                                    className="block w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                    placeholder="请输入密码"
                                    value={formData.password}
                                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                                />
                                <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                                    <button type="button" onClick={() => setShowPassword(!showPassword)} className="text-gray-400 hover:text-gray-500">
                                        {showPassword ? <EyeOff className="h-5 w-5"/> : <Eye className="h-5 w-5"/>}
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* 验证码区域 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700">验证码 / Verification Code</label>
                            <div className="mt-1 flex gap-3">
                                <div className="relative rounded-md shadow-sm flex-1">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <ShieldCheck className="h-5 w-5 text-gray-400"/>
                                    </div>
                                    <input
                                        type="text"
                                        required
                                        maxLength={4}
                                        className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 sm:text-sm tracking-widest uppercase"
                                        placeholder="请输入右侧验证码"
                                        value={formData.captchaInput}
                                        onChange={(e) => setFormData({...formData, captchaInput: e.target.value})}
                                    />
                                </div>
                                {/* 验证码图片+刷新 */}
                                <div className="relative group cursor-pointer" onClick={refreshCaptcha}>
                                    <img
                                        src={captcha.dataUrl || null}
                                        alt="Captcha"
                                        className="h-[46px] w-[120px] rounded-lg border border-gray-200 object-cover"
                                    />
                                    <div className="absolute inset-0 bg-black/5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                        <RefreshCw className="text-blue-600 font-bold" size={20}/>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* 登录按钮 */}
                        <button
                            type="submit"
                            disabled={loading}
                            className={`w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
                        >
                            {loading ? '登录中...' : <span className="flex items-center"><ShieldCheck className="mr-2 h-5 w-5"/> 登录</span>}
                        </button>
                    </form>

                    <div className="mt-6 text-center text-xs text-gray-400">
                        点击图片可刷新验证码
                    </div>
                </div>
            </div>
        </div>
    );
};

export default StudentLogin;