import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, BookOpen, Clock, Activity, MoreHorizontal, LogOut, LayoutDashboard } from 'lucide-react';

const StatCard = ({ title, value, icon: Icon, color, trend }) => (
    <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-4">
            <div className={`p-3 rounded-lg ${color}`}>
                <Icon size={24} className="text-white" />
            </div>
            <span className="text-green-500 text-sm font-medium flex items-center gap-1">
        <Activity size={14} /> {trend}
      </span>
        </div>
        <h3 className="text-gray-500 text-sm font-medium">{title}</h3>
        <p className="text-3xl font-bold text-gray-800 mt-1">{value}</p>
    </div>
);

const TeacherDashboard = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState({ name: '加载中...', id: '' });

    // 🛡️ 页面加载时：检查登录状态并读取用户信息
    useEffect(() => {
        const token = localStorage.getItem('authToken');
        const userInfoStr = localStorage.getItem('userInfo');

        if (!token) {
            // 如果没有 Token，踢回登录页
            navigate('/teacher/login');
            return;
        }

        if (userInfoStr) {
            try {
                const parsedUser = JSON.parse(userInfoStr);
                setUser(parsedUser);
            } catch (e) {
                console.error("解析用户信息失败", e);
            }
        }
    }, [navigate]);

    // 🚪 登出功能
    const handleLogout = () => {
        if (window.confirm('确定要退出登录吗？')) {
            localStorage.removeItem('authToken');
            localStorage.removeItem('userInfo');
            navigate('/teacher/login');
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            {/* 顶部 Header */}
            <header className="mb-8 flex justify-between items-center bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                <div className="flex items-center gap-4">
                    <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                        <LayoutDashboard size={24} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800">教学仪表盘</h1>
                        <p className="text-gray-500 text-sm">
                            欢迎回来，<span className="font-bold text-indigo-600">{user.name}</span> (ID: {user.id})
                        </p>
                    </div>
                </div>

                <div className="flex gap-3">
                    <button
                        onClick={handleLogout}
                        className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-red-50 hover:text-red-600 rounded-lg transition-colors border border-transparent hover:border-red-100"
                    >
                        <LogOut size={18} />
                        退出
                    </button>
                    <button className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors shadow-sm">
                        发布新任务
                    </button>
                </div>
            </header>

            {/* 数据概览卡片 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <StatCard title="活跃学生" value="32" icon={Users} color="bg-blue-500" trend="+12%" />
                <StatCard title="今日对话数" value="1,240" icon={BookOpen} color="bg-indigo-500" trend="+5%" />
                <StatCard title="平均学习时长" value="45m" icon={Clock} color="bg-orange-500" trend="+8%" />
                <StatCard title="作业完成率" value="89%" icon={Activity} color="bg-green-500" trend="+2%" />
            </div>

            {/* 学生列表区域 */}
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
                <div className="p-6 border-b border-gray-100 flex justify-between items-center">
                    <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                        <Users size={20} className="text-gray-400" />
                        学生学习进度监控
                    </h2>
                    <button className="text-indigo-600 text-sm font-medium hover:underline">查看全部</button>
                </div>
                <table className="w-full">
                    <thead className="bg-gray-50 text-left">
                    <tr>
                        <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">学生信息</th>
                        <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">当前状态</th>
                        <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">最近活跃话题</th>
                        <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">AI 交互数</th>
                        <th className="px-6 py-4"></th>
                    </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                    {[1, 2, 3, 4].map((item) => (
                        <tr key={item} className="hover:bg-gray-50 transition-colors">
                            <td className="px-6 py-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600 text-sm font-bold">
                                        S{item}
                                    </div>
                                    <div>
                                        <span className="font-medium text-gray-700 block">学生 {item}号</span>
                                        <span className="text-xs text-gray-400">2025级 软件工程</span>
                                    </div>
                                </div>
                            </td>
                            <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${item % 2 === 0 ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                    {item % 2 === 0 ? '在线学习中' : '离线'}
                  </span>
                            </td>
                            <td className="px-6 py-4 text-gray-600 text-sm">
                                {item === 1 ? '德语被动语态练习' : '基础发音纠正'}
                            </td>
                            <td className="px-6 py-4 text-gray-800 font-medium">{100 + item * 23}</td>
                            <td className="px-6 py-4 text-right">
                                <button className="text-gray-400 hover:text-indigo-600 transition-colors">
                                    <MoreHorizontal size={20} />
                                </button>
                            </td>
                        </tr>
                    ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default TeacherDashboard;