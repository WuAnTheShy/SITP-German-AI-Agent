import React, {useState, useEffect} from 'react';
import {useNavigate} from 'react-router-dom';
import axios from 'axios';
import {
    LayoutDashboard, Users, GraduationCap, Clock,
    ArrowRight, Plus, Search, MoreVertical, Loader2,
    TrendingUp, Award, Activity
} from 'lucide-react';

// ----------------------------------------------------------------------
// 🔧 配置区域
// ----------------------------------------------------------------------
// ⚠️ 请确保此地址与您 Apifox 中的 Mock 地址一致
const MOCK_SERVER_BASE = 'https://m1.apifoxmock.com/m1/7746497-7491372-default';
const API_DASHBOARD = `${MOCK_SERVER_BASE}/api/teacher/dashboard`;

const TeacherDashboard = () => {
    const navigate = useNavigate();

    // 状态管理
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState(null);
    const [error, setError] = useState('');
    const [searchTerm, setSearchTerm] = useState('');

    // 🟢 初始化：获取仪表盘数据
    useEffect(() => {
        const fetchDashboardData = async () => {
            setLoading(true);
            try {
                console.log('[Client] 正在加载仪表盘数据...');
                const response = await axios.get(API_DASHBOARD);

                if (response.data.code === 200) {
                    setData(response.data.data);
                } else {
                    throw new Error(response.data.message || '数据加载失败');
                }
            } catch (err) {
                console.error('加载失败:', err);
                // 降级数据（防止页面白屏）
                setData(FALLBACK_DATA);
                setError('网络请求失败，已切换至离线模式');
            } finally {
                setLoading(false);
            }
        };

        fetchDashboardData();
    }, []);

    // 过滤学生列表
    const filteredStudents = data?.students?.filter(s =>
        s.name.includes(searchTerm) || s.uid.includes(searchTerm)
    ) || [];

    // 渲染加载状态
    if (loading) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
                <Loader2 size={40} className="text-indigo-600 animate-spin mb-4"/>
                <p className="text-gray-500 font-medium">正在同步班级学情数据...</p>
            </div>
        );
    }

    // 渲染主界面
    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-7xl mx-auto space-y-8">

                {/* 1. 顶部 Header */}
                <div className="flex justify-between items-end">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                            <LayoutDashboard className="text-indigo-600"/>
                            教师控制台
                            {/* 🟢 动态班级名称 */}
                            <span className="text-sm font-normal text-gray-500 bg-gray-200 px-2 py-0.5 rounded-md">
                                {data?.className || '加载中...'}
                            </span>
                        </h1>
                        <p className="text-gray-500 mt-2">欢迎回来，{data?.teacherName || '老师'}。今日有 {data?.pendingTasks || 0} 条新的学情动态待处理。</p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={() => navigate('/teacher/scenario')}
                            className="bg-indigo-600 text-white px-5 py-2.5 rounded-xl font-bold hover:bg-indigo-700 transition-all flex items-center gap-2 shadow-sm hover:shadow-md hover:-translate-y-0.5"
                        >
                            <Plus size={18}/> 发布情景任务
                        </button>
                        <button
                            onClick={() => navigate('/teacher/exam')}
                            className="bg-white text-indigo-600 border border-indigo-100 px-5 py-2.5 rounded-xl font-bold hover:bg-indigo-50 transition-all flex items-center gap-2"
                        >
                            <GraduationCap size={18}/> 生成试卷
                        </button>
                    </div>
                </div>

                {/* 错误提示 */}
                {error && (
                    <div className="bg-orange-50 text-orange-600 px-4 py-3 rounded-xl flex items-center gap-2 border border-orange-100">
                        <Activity size={18}/> {error}
                    </div>
                )}

                {/* 2. 核心指标卡片 (Stats) - 🟢 全部动态化 */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <StatCard
                        icon={<Users className="text-blue-600"/>}
                        label="班级总人数"
                        value={data?.stats?.totalStudents || 0}
                        trend={data?.stats?.totalStudentsTrend || '-'} // 动态趋势
                        bg="bg-blue-50"
                    />
                    <StatCard
                        icon={<Clock className="text-purple-600"/>}
                        label="人均互动时长"
                        value={`${data?.stats?.avgDuration || 0}h`}
                        trend={data?.stats?.avgDurationTrend || '-'} // 动态趋势
                        bg="bg-purple-50"
                    />
                    <StatCard
                        icon={<Award className="text-orange-600"/>}
                        label="平均综合得分"
                        value={data?.stats?.avgScore || 0}
                        trend={data?.stats?.avgScoreTrend || '-'} // 动态趋势
                        bg="bg-orange-50"
                    />
                    <StatCard
                        icon={<TrendingUp className="text-green-600"/>}
                        label="任务完成率"
                        value={`${data?.stats?.completionRate || 0}%`}
                        trend={data?.stats?.completionRateTrend || '-'} // 动态趋势
                        bg="bg-green-50"
                    />
                </div>

                {/* 3. 学生列表区块 */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                    {/* 列表头部工具栏 */}
                    <div className="p-6 border-b border-gray-100 flex justify-between items-center">
                        <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                            <Users size={20} className="text-indigo-600"/> 学情监控列表
                        </h2>
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18}/>
                            <input
                                type="text"
                                placeholder="搜索姓名或学号..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 w-64 transition-all"
                            />
                        </div>
                    </div>

                    {/* 表格 */}
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50 border-b border-gray-100">
                            <tr>
                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">学生信息</th>
                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">活跃度</th>
                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">综合评分</th>
                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">薄弱环节</th>
                                <th className="px-6 py-4 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">操作</th>
                            </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                            {filteredStudents.map((student) => (
                                <tr
                                    key={student.uid}
                                    onClick={() => navigate(`/teacher/student/${student.uid}`, {state: {student}})}
                                    className="hover:bg-indigo-50/50 transition-colors cursor-pointer group"
                                >
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center">
                                            <div className="flex-shrink-0 h-10 w-10 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600 font-bold">
                                                {student.name[0]}
                                            </div>
                                            <div className="ml-4">
                                                <div className="text-sm font-bold text-gray-900">{student.name}</div>
                                                <div className="text-xs text-gray-500">{student.uid}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center gap-2">
                                            <div className="w-16 h-2 bg-gray-100 rounded-full overflow-hidden">
                                                <div className="h-full bg-green-500" style={{width: `${student.active}%`}}></div>
                                            </div>
                                            <span className="text-sm text-gray-600">{student.active}%</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                                student.score >= 90 ? 'bg-green-100 text-green-800' :
                                                student.score >= 80 ? 'bg-blue-100 text-blue-800' :
                                                'bg-orange-100 text-orange-800'
                                            }`}>
                                                {student.score} 分
                                            </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            <span className="flex items-center gap-1 text-red-500 bg-red-50 px-2 py-0.5 rounded w-fit">
                                                <Activity size={12}/> {student.weak || '暂无'}
                                            </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button className="text-indigo-600 hover:text-indigo-900 p-2 hover:bg-indigo-50 rounded-lg transition-colors">
                                            <ArrowRight size={18}/>
                                        </button>
                                    </td>
                                </tr>
                            ))}
                            </tbody>
                        </table>
                    </div>
                    {filteredStudents.length === 0 && (
                        <div className="p-12 text-center text-gray-500">未找到匹配的学生</div>
                    )}
                </div>
            </div>
        </div>
    );
};

// 子组件：指标卡片 (支持 trend 颜色变化逻辑)
const StatCard = ({icon, label, value, trend, bg}) => {
    // 简单的逻辑判断趋势颜色：以 "+" 或 "↑" 开头为绿色，否则为中性色
    const isPositive = trend.includes('+') || trend.includes('↑');

    return (
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start mb-4">
                <div className={`p-3 rounded-xl ${bg}`}>{icon}</div>
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${isPositive ? 'text-green-600 bg-green-50' : 'text-gray-600 bg-gray-50'}`}>
                    {trend}
                </span>
            </div>
            <div className="text-2xl font-bold text-gray-900 mb-1">{value}</div>
            <div className="text-xs text-gray-500">{label}</div>
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
        {name: '演示学生A', uid: '2452001', class: '软件工程', active: 90, score: 95, weak: '虚拟式'},
        {name: '演示学生B', uid: '2452002', class: '软件工程', active: 65, score: 78, weak: '被动语态'}
    ]
};

export default TeacherDashboard;