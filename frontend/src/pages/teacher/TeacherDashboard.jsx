import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import request from '../../api/request';
import { LayoutDashboard, LogOut, Users, FileText, Settings, Activity, ArrowRight, TrendingUp, Clock, BookOpen, Search, Zap, Loader2, Bot, RefreshCw, Plus, GraduationCap, Award } from 'lucide-react';
import { API_DASHBOARD } from '../../api/config';
import { useToast } from '../../components/Toast';

const TeacherDashboard = () => {
    const navigate = useNavigate();
    const toast = useToast();

    // 状态管理
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState(null);
    const [error, setError] = useState('');
    const [searchTerm, setSearchTerm] = useState('');
    const [refreshing, setRefreshing] = useState(false);

    // 🟢 从 localStorage 读取教师名称
    const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
    const teacherName = userInfo.name || data?.teacherName || '老师';

    // 🟢 获取仪表盘数据（可复用）
    const fetchDashboardData = useCallback(async (showRefreshToast = false) => {
        if (showRefreshToast) setRefreshing(true);
        else setLoading(true);

        try {
            console.log('[Client] 正在加载仪表盘数据...');
            const response = await request.get(API_DASHBOARD);

            if (response.data.code === 200) {
                setData(response.data.data);
                setError('');
                if (showRefreshToast) toast.success('数据刷新成功');
            } else {
                throw new Error(response.data.message || '数据加载失败');
            }
        } catch (err) {
            console.error('加载失败:', err);
            // 降级数据（防止页面白屏）
            setData(FALLBACK_DATA);
            setError('网络请求失败，已切换至离线模式');
            if (showRefreshToast) toast.error('刷新失败，使用缓存数据');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, [toast]);

    // 初始化
    useEffect(() => {
        fetchDashboardData(false);
    }, [fetchDashboardData]);

    // 🟢 登出
    const handleLogout = () => {
        localStorage.removeItem('authToken');
        localStorage.removeItem('userInfo');
        toast.info('已安全退出');
        setTimeout(() => navigate('/'), 500);
    };

    // 过滤学生列表（增加判空容错和大小写不敏感搜索）
    const filteredStudents = data?.students?.filter(s => {
        const nameMatch = s?.name ? s.name.toLowerCase().includes(searchTerm.toLowerCase()) : false;
        const uidMatch = s?.uid ? String(s.uid).toLowerCase().includes(searchTerm.toLowerCase()) : false;
        return nameMatch || uidMatch;
    }) || [];

    // 渲染加载状态
    if (loading) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-900">
                <Loader2 size={40} className="text-indigo-600 dark:text-indigo-400 animate-spin mb-4" />
                <p className="text-gray-500 dark:text-gray-400 font-medium">正在同步班级学情数据...</p>
            </div>
        );
    }

    // 渲染主界面
    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
            <div className="max-w-7xl mx-auto space-y-8">

                {/* 1. 顶部 Header */}
                <div className="flex justify-between items-end">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-3">
                            <LayoutDashboard className="text-indigo-600 dark:text-indigo-400" />
                            教师控制台
                            {/* 🟢 动态班级名称 */}
                            <span className="text-sm font-normal text-gray-500 dark:text-gray-400 bg-gray-200 dark:bg-gray-700 px-2 py-0.5 rounded-md">
                                {data?.className || '加载中...'}
                            </span>
                        </h1>
                        <p className="text-gray-500 dark:text-gray-400 mt-2">欢迎回来，{teacherName}。今日有 {data?.pendingTasks || 0} 条新的学情动态待处理。</p>
                    </div>
                    <div className="flex gap-3">
                        {/* 🟢 刷新按钮 */}
                        <button
                            onClick={() => fetchDashboardData(true)}
                            disabled={refreshing}
                            className="bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700 px-4 py-2.5 rounded-xl font-medium hover:bg-gray-50 dark:bg-gray-900 transition-all flex items-center gap-2 disabled:opacity-50"
                        >
                            <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} /> 刷新
                        </button>
                        <button
                            onClick={() => navigate('/teacher/scenario')}
                            className="bg-indigo-600 text-white px-5 py-2.5 rounded-xl font-bold hover:bg-indigo-700 transition-all flex items-center gap-2 shadow-sm dark:shadow-gray-900/50 hover:shadow-md dark:shadow-gray-900/50 hover:-translate-y-0.5"
                        >
                            <Plus size={18} /> 发布情景任务
                        </button>
                        <button
                            onClick={() => navigate('/teacher/ai')}
                            className="bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400 px-5 py-2.5 rounded-xl font-bold hover:bg-indigo-100 transition-all flex items-center gap-2 shadow-sm dark:shadow-gray-900/50"
                        >
                            <Bot size={18} /> AI 教研助手
                        </button>
                        <button
                            onClick={() => navigate('/teacher/history')}
                            className="bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 border border-indigo-100 dark:border-indigo-800/50 px-5 py-2.5 rounded-xl font-bold hover:bg-indigo-50 dark:bg-indigo-900/30 transition-all flex items-center gap-2"
                        >
                            <FileText size={18} /> 发布记录
                        </button>
                        <button
                            onClick={() => navigate('/teacher/exam')}
                            className="bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 border border-indigo-100 dark:border-indigo-800/50 px-5 py-2.5 rounded-xl font-bold hover:bg-indigo-50 dark:bg-indigo-900/30 transition-all flex items-center gap-2"
                        >
                            <GraduationCap size={18} /> 生成试卷
                        </button>
                        {/* 🟢 登出按钮 */}
                        <button
                            onClick={handleLogout}
                            className="bg-white dark:bg-gray-800 text-red-500 border border-red-100 px-4 py-2.5 rounded-xl font-medium hover:bg-red-50 dark:bg-red-900/30 transition-all flex items-center gap-2"
                        >
                            <LogOut size={16} /> 退出
                        </button>
                    </div>
                </div>

                {/* 错误提示 */}
                {error && (
                    <div className="bg-orange-50 dark:bg-orange-900/30 text-orange-600 px-4 py-3 rounded-xl flex items-center gap-2 border border-orange-100">
                        <Activity size={18} /> {error}
                    </div>
                )}

                {/* 2. 核心指标卡片 (Stats) - 🟢 全部动态化 */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <StatCard
                        icon={<Users className="text-blue-600 dark:text-blue-400" />}
                        label="班级总人数"
                        value={data?.stats?.totalStudents || 0}
                        trend={data?.stats?.totalStudentsTrend || '-'} // 动态趋势
                        bg="bg-blue-50 dark:bg-blue-900/30"
                    />
                    <StatCard
                        icon={<Clock className="text-purple-600" />}
                        label="人均互动时长"
                        value={`${data?.stats?.avgDuration || 0} h`}
                        trend={data?.stats?.avgDurationTrend || '-'} // 动态趋势
                        bg="bg-purple-50 dark:bg-purple-900/30"
                    />
                    <StatCard
                        icon={<Award className="text-orange-600" />}
                        label="平均综合得分"
                        value={data?.stats?.avgScore || 0}
                        trend={data?.stats?.avgScoreTrend || '-'} // 动态趋势
                        bg="bg-orange-50 dark:bg-orange-900/30"
                    />
                    <StatCard
                        icon={<TrendingUp className="text-green-600" />}
                        label="任务完成率"
                        value={`${data?.stats?.completionRate || 0}% `}
                        trend={data?.stats?.completionRateTrend || '-'} // 动态趋势
                        bg="bg-green-50 dark:bg-green-900/30"
                    />
                </div>

                {/* 3. 学生列表区块 */}
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm dark:shadow-gray-900/50 border border-gray-100 dark:border-gray-700 overflow-hidden">
                    {/* 列表头部工具栏 */}
                    <div className="p-6 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
                        <h2 className="text-lg font-bold text-gray-800 dark:text-gray-200 flex items-center gap-2">
                            <Users size={20} className="text-indigo-600 dark:text-indigo-400" /> 学情监控列表
                        </h2>
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500" size={18} />
                            <input
                                className="dark:text-white" type="text"
                                placeholder="搜索姓名或学号..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 w-64 transition-all"
                            />
                        </div>
                    </div>

                    {/* 表格 */}
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-100 dark:border-gray-700">
                                <tr>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">学生信息</th>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">活跃度</th>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">综合评分</th>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">薄弱环节</th>
                                    <th className="px-6 py-4 text-right text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">操作</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                                {filteredStudents.map((student) => (
                                    <tr
                                        key={student.uid}
                                        onClick={() => navigate(`/teacher/student/${student.uid}`, { state: { student } })}
                                        className="hover:bg-indigo-50 dark:bg-indigo-900/30/50 transition-colors cursor-pointer group"
                                    >
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                <div className="flex-shrink-0 h-10 w-10 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600 dark:text-indigo-400 font-bold">
                                                    {(student.name || '匿')[0]}
                                                </div>
                                                <div className="ml-4">
                                                    <div className="text-sm font-bold text-gray-900 dark:text-gray-100">{student.name || '匿名用户'}</div>
                                                    <div className="text-xs text-gray-500 dark:text-gray-400">{student.uid || '无学号'}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center gap-2">
                                                <div className="w-16 h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                                                    <div className="h-full bg-green-500" style={{ width: `${student.active}% ` }}></div>
                                                </div>
                                                <span className="text-sm text-gray-600 dark:text-gray-400">{student.active}%</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${student.score >= 90 ? 'bg-green-100 text-green-800' :
                                                student.score >= 80 ? 'bg-blue-100 text-blue-800' :
                                                    'bg-orange-100 text-orange-800'
                                                }`}>
                                                {student.score} 分
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                            <span className="flex items-center gap-1 text-red-500 bg-red-50 dark:bg-red-900/30 px-2 py-0.5 rounded w-fit">
                                                <Activity size={12} /> {student.weak || '暂无'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <button className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 p-2 hover:bg-indigo-50 dark:bg-indigo-900/30 rounded-lg transition-colors">
                                                <ArrowRight size={18} />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    {filteredStudents.length === 0 && (
                        <div className="p-12 text-center text-gray-500 dark:text-gray-400">未找到匹配的学生</div>
                    )}
                </div>
            </div>
        </div>
    );
};

// 子组件：指标卡片 (支持 trend 颜色变化逻辑)
const StatCard = ({ icon, label, value, trend, bg }) => {
    // 简单的逻辑判断趋势颜色：以 "+" 或 "↑" 开头为绿色，否则为中性色
    const isPositive = trend.includes('+') || trend.includes('↑');

    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm dark:shadow-gray-900/50 border border-gray-100 dark:border-gray-700 hover:shadow-md dark:shadow-gray-900/50 transition-shadow">
            <div className="flex justify-between items-start mb-4">
                <div className={`p-3 rounded-xl ${bg}`}>{icon}</div>
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${isPositive ? 'text-green-600 bg-green-50 dark:bg-green-900/30' : 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900'}`}>
                    {trend}
                </span>
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1">{value}</div>
            <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
        </div>
    );
};

// 兜底数据 (更新了字段以匹配新结构)
const FALLBACK_DATA = {
    teacherName: '张老师 (离线)',
    className: '软件工程(四)班',
    pendingTasks: 3,
    stats: {
        totalStudents: 45, totalStudentsTrend: '+0',
        avgDuration: 12.5, avgDurationTrend: '↑ 2%',
        avgScore: 88.2, avgScoreTrend: '↑ 0.5',
        completionRate: 95, completionRateTrend: '稳定'
    },
    students: [
        { name: '演示学生A', uid: '2452001', class: '软件工程', active: 90, score: 95, weak: '虚拟式' },
        { name: '演示学生B', uid: '2452002', class: '软件工程', active: 65, score: 78, weak: '被动语态' }
    ]
};

export default TeacherDashboard;