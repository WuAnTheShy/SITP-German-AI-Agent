import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { School, Lock, User, ArrowLeft, Eye, EyeOff, ShieldCheck, AlertCircle, RefreshCw } from 'lucide-react';
import { API_LOGIN as API_LOGIN_URL } from '../../api/config';

const TeacherLogin = () => {
    const navigate = useNavigate();
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // 🔐 验证码状态
    const [captcha, setCaptcha] = useState({ code: '', dataUrl: '' });

    const [formData, setFormData] = useState({
        employeeId: '',
        password: '',
        captchaInput: '' // 新增验证码输入字段
    });

    // 🎨 生成本地图形验证码 (Canvas)
    const refreshCaptcha = () => {
        const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // 去除易混淆字符 I, O, 0, 1
        let code = '';
        for (let i = 0; i < 4; i++) {
            code += chars.charAt(Math.floor(Math.random() * chars.length));
        }

        const canvas = document.createElement('canvas');
        canvas.width = 120;
        canvas.height = 40;
        const ctx = canvas.getContext('2d');

        // 1. 绘制背景
        ctx.fillStyle = '#F3F4F6'; // 浅灰色背景
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // 2. 绘制干扰线
        for (let i = 0; i < 7; i++) {
            ctx.strokeStyle = `rgba(0, 0, 0, ${Math.random() * 0.2})`;
            ctx.beginPath();
            ctx.moveTo(Math.random() * canvas.width, Math.random() * canvas.height);
            ctx.lineTo(Math.random() * canvas.width, Math.random() * canvas.height);
            ctx.stroke();
        }

        // 3. 绘制文字 (带随机旋转和颜色)
        ctx.font = 'bold 24px sans-serif';
        ctx.textBaseline = 'middle';
        const startX = 20;
        for (let i = 0; i < 4; i++) {
            const char = code[i];
            ctx.save();
            // 随机位置和旋转
            const x = startX + i * 25;
            const y = canvas.height / 2 + (Math.random() - 0.5) * 10;
            const angle = (Math.random() - 0.5) * 0.5; // -0.25 到 0.25 弧度

            ctx.translate(x, y);
            ctx.rotate(angle);
            ctx.fillStyle = `hsl(${Math.random() * 360}, 60%, 40%)`; // 随机深色
            ctx.fillText(char, 0, 0);
            ctx.restore();
        }

        setCaptcha({ code: code, dataUrl: canvas.toDataURL() });
    };

    // 初始化时生成验证码
    useEffect(() => {
        refreshCaptcha();
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        // 🛑 第一步：先校验验证码
        if (formData.captchaInput.toUpperCase() !== captcha.code) {
            setError('验证码错误，请重新输入');
            setLoading(false);
            refreshCaptcha(); // 输错后自动刷新
            setFormData(prev => ({ ...prev, captchaInput: '' })); // 清空输入框
            return;
        }

        try {
            console.log("🔵 [调试] 请求地址:", API_LOGIN_URL);

            const response = await axios.post(API_LOGIN_URL, {
                username: formData.employeeId,
                password: formData.password
            });

            console.log("🟢 [调试] 服务器返回:", response.data);

            let token = response.data.token || response.data.data?.token;
            let mockUser = response.data.user || response.data.data?.user;

            if (!token) {
                throw new Error("登录成功，但未找到 Token");
            }

            // 构造显示的 User 对象
            // TODO 优化安全性
            const displayUser = {
                ...mockUser,
                id: formData.employeeId,
                name: mockUser.name,
                role: 'teacher'
            };

            localStorage.setItem('authToken', token);
            localStorage.setItem('userInfo', JSON.stringify(displayUser));

            navigate('/teacher/dashboard');

        } catch (err) {
            console.error('🔴 登录错误:', err);
            // 登录失败也要刷新验证码，防止重放
            refreshCaptcha();
            setFormData(prev => ({ ...prev, captchaInput: '' }));

            if (err.response) {
                setError(`登录失败: ${err.response.data.message || '服务器拒绝'}`);
            } else if (err.request) {
                setError('无法连接服务器 (网络/跨域错误)');
            } else {
                setError(err.message || '未知错误');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
            <div className="sm:mx-auto sm:w-full sm:max-w-md mb-6 px-4">
                <button
                    onClick={() => navigate('/')}
                    className="flex items-center text-gray-500 hover:text-indigo-600 transition-colors text-sm font-medium"
                >
                    <ArrowLeft size={16} className="mr-1" /> 返回首页
                </button>
            </div>

            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <div className="flex justify-center">
                    <div className="h-16 w-16 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg transform rotate-3">
                        <School className="text-white h-8 w-8" />
                    </div>
                </div>
                <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">教师端登录</h2>
            </div>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                <div className="bg-white py-8 px-4 shadow-xl sm:rounded-lg sm:px-10 border border-gray-100">
                    {error && (
                        <div className="mb-4 bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg flex items-start">
                            <AlertCircle className="h-5 w-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" />
                            <p className="text-sm text-red-700">{error}</p>
                        </div>
                    )}

                    <form className="space-y-6" onSubmit={handleSubmit}>
                        {/* 工号输入 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700">工号 / Employee ID</label>
                            <div className="mt-1 relative rounded-md shadow-sm">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <User className="h-5 w-5 text-gray-400" />
                                </div>
                                <input
                                    type="text"
                                    required
                                    className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                    placeholder="请输入工号或用户 ID"
                                    value={formData.employeeId}
                                    onChange={(e) => setFormData({ ...formData, employeeId: e.target.value })}
                                />
                            </div>
                        </div>

                        {/* 密码输入 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700">密码 / Password</label>
                            <div className="mt-1 relative rounded-md shadow-sm">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Lock className="h-5 w-5 text-gray-400" />
                                </div>
                                <input
                                    type={showPassword ? "text" : "password"}
                                    required
                                    className="block w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                    placeholder="请输入密码"
                                    value={formData.password}
                                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                />
                                <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                                    <button type="button" onClick={() => setShowPassword(!showPassword)} className="text-gray-400 hover:text-gray-500">
                                        {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* 🛡️ 新增：验证码区域 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700">验证码 / Verification Code</label>
                            <div className="mt-1 flex gap-3">
                                <div className="relative rounded-md shadow-sm flex-1">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <ShieldCheck className="h-5 w-5 text-gray-400" />
                                    </div>
                                    <input
                                        type="text"
                                        required
                                        maxLength={4}
                                        className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm tracking-widest uppercase"
                                        placeholder="请输入右侧验证码"
                                        value={formData.captchaInput}
                                        onChange={(e) => setFormData({ ...formData, captchaInput: e.target.value })}
                                    />
                                </div>
                                {/* 验证码图片与刷新按钮 */}
                                <div className="relative group cursor-pointer" onClick={refreshCaptcha}>
                                    <img
                                        src={captcha.dataUrl || null}
                                        alt="Captcha"
                                        className="h-[46px] w-[120px] rounded-lg border border-gray-200 object-cover"
                                    />
                                    {/* 悬停时显示刷新图标 */}
                                    <div className="absolute inset-0 bg-black/5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                        <RefreshCw className="text-indigo-600 font-bold" size={20} />
                                    </div>
                                </div>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className={`w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
                        >
                            {loading ? '登录中...' : <span className="flex items-center"><ShieldCheck className="mr-2 h-5 w-5" /> 登录</span>}
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

export default TeacherLogin;