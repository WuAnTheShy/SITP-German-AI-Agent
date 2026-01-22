import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Users, Activity, LogOut, LayoutDashboard,
    Brain, FileText, MessageSquare, AlertCircle,
    Wand2, BarChart3, Mic, Globe
} from 'lucide-react';

// 组件：智能工具卡片
const SmartToolCard = ({ title, desc, icon: Icon, color, onClick, badge }) => (
    <div
        onClick={onClick}
        className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm hover:shadow-md hover:border-indigo-100 transition-all cursor-pointer group relative overflow-hidden"
    >
        <div className={`absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity ${color.text}`}>
            <Icon size={80} />
        </div>
        <div className="flex items-start gap-4">
            <div className={`p-3 rounded-xl ${color.bg} ${color.text}`}>
                <Icon size={24} />
            </div>
            <div>
                <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                    {title}
                    {badge && <span className="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full">{badge}</span>}
                </h3>
                <p className="text-sm text-gray-500 mt-1 leading-relaxed">{desc}</p>
            </div>
        </div>
        <div className="mt-4 flex items-center text-sm font-medium text-indigo-600 opacity-0 group-hover:opacity-100 transition-opacity">
            点击进入配置 <Wand2 size={14} className="ml-1" />
        </div>
    </div>
);

// 组件：数据卡片
const StatCard = ({ title, value, subtext, icon: Icon, trend }) => (
    <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
        <div className="flex justify-between items-start mb-2">
            <div className="p-2 bg-gray-50 rounded-lg text-gray-400">
                <Icon size={20} />
            </div>
            {trend && (
                <span className="flex items-center text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full">
          {trend}
        </span>
            )}
        </div>
        <div className="text-2xl font-bold text-gray-800">{value}</div>
        <div className="text-xs text-gray-500 mt-1">{title}</div>
        {subtext && <div className="text-xs text-indigo-500 mt-2 font-medium">{subtext}</div>}
    </div>
);

const TeacherDashboard = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState({ name: '加载中...', id: '' });

    // ------------------------------------------------------------------
    // 📝 模拟学生数据 (新增 homeworks 字段)
    // ------------------------------------------------------------------
    const students = [
        {
            id: 1, name: '张伟', uid: '2452201', weak: '发音辨识', path: '语音纠正专项', status: '进行中', score: 85, active: 92,
            homeworks: [
                { id: 101, title: 'Unit 1: 德语字母发音', status: '已完成', score: 92, date: '2025-12-01', feedback: '元音饱满，非常棒！' },
                { id: 102, title: '情景对话：自我介绍', status: '已完成', score: 88, date: '2025-12-05', feedback: '语调自然，注意语速。' },
                { id: 103, title: '语法：动词变位测试', status: '待订正', score: 75, date: '2025-12-10', feedback: '不规则动词变位有误。' },
                { id: 104, title: 'Unit 3: 餐厅点餐', status: '进行中', score: null, date: '2025-12-15', feedback: '尚未提交' }
            ]
        },
        {
            id: 2, name: '李娜', uid: '2452202', weak: '复杂从句', path: 'B1 阅读强化', status: '已完成', score: 92, active: 88,
            homeworks: [
                { id: 201, title: 'Unit 1: 德语字母发音', status: '已完成', score: 95, date: '2025-12-01', feedback: '完美！' },
                { id: 202, title: '阅读理解：德国文化', status: '已完成', score: 90, date: '2025-12-08', feedback: '理解深刻。' },
                { id: 203, title: '写作：我的假期', status: '已完成', score: 94, date: '2025-12-14', feedback: '从句使用非常地道。' }
            ]
        },
        {
            id: 3, name: '王强', uid: '2452203', weak: '词汇量不足', path: '高频词汇冲刺', status: '进行中', score: 76, active: 65,
            homeworks: [
                { id: 301, title: 'Unit 1: 基础词汇听写', status: '已完成', score: 65, date: '2025-12-02', feedback: '需加强名词词性记忆。' },
                { id: 302, title: 'Unit 2: 动词填空', status: '逾期补交', score: 70, date: '2025-12-09', feedback: '注意按时提交。' },
                { id: 303, title: '词汇：交通工具', status: '未提交', score: null, date: '2025-12-15', feedback: '请尽快完成。' }
            ]
        },
        {
            id: 4, name: '赵敏', uid: '2452204', weak: '虚拟语气', path: '语法深度解析', status: '未开始', score: 88, active: 75,
            homeworks: [
                { id: 401, title: '语法：虚拟式II', status: '已完成', score: 85, date: '2025-12-12', feedback: '概念理解正确。' },
                { id: 402, title: '情景改写：如果我是...', status: '进行中', score: null, date: '2025-12-16', feedback: '等待提交' }
            ]
        },
    ];

    useEffect(() => {
        const token = localStorage.getItem('authToken');
        const userInfoStr = localStorage.getItem('userInfo');
        if (!token) { navigate('/teacher/login'); return; }
        if (userInfoStr) setUser(JSON.parse(userInfoStr));
    }, [navigate]);

    const handleLogout = () => {
        if (window.confirm('确定要退出登录吗？')) {
            localStorage.clear();
            navigate('/teacher/login');
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 p-6 md:p-8">
            {/* Header */}
            <header className="mb-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white p-5 rounded-2xl shadow-sm border border-gray-100">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-indigo-600 rounded-xl flex items-center justify-center text-white shadow-indigo-200 shadow-lg">
                        <LayoutDashboard size={24} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800">德语教学驾驶舱</h1>
                        <p className="text-gray-500 text-sm">
                            当前学期：2025-2026 春季 | <span className="text-indigo-600 font-medium">{user.name}</span>
                        </p>
                    </div>
                </div>
                <button onClick={handleLogout} className="flex items-center gap-2 px-4 py-2 text-gray-500 hover:bg-red-50 hover:text-red-600 rounded-lg transition-colors text-sm font-medium">
                    <LogOut size={18} /> 退出系统
                </button>
            </header>

            {/* 核心功能入口 */}
            <div className="mb-8">
                <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                    <Brain className="text-indigo-600" size={20} /> AI 智能教学助手
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <SmartToolCard
                        title="发布情景模拟活动"
                        desc="配置 AI 陪练角色与场景（如：慕尼黑问路），强化口语产出。"
                        icon={MessageSquare}
                        color={{ bg: 'bg-purple-100', text: 'text-purple-600' }}
                        badge="高频使用"
                        onClick={() => navigate('/teacher/scenario')}
                    />
                    <SmartToolCard
                        title="一键生成差异化试卷"
                        desc="基于学情数据，自动生成千人千面的针对性补强练习。"
                        icon={FileText}
                        color={{ bg: 'bg-blue-100', text: 'text-blue-600' }}
                        onClick={() => navigate('/teacher/exam')}
                    />
                </div>
            </div>

            {/* 数据概览 */}
            <div className="mb-8">
                <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                    <Activity className="text-indigo-600" size={20} /> 全班学情概览
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <StatCard title="AI 互动总时长" value="128h" subtext="本周 +12%" icon={Users} trend="活跃" />
                    <StatCard title="口语能力均分" value="B1.2" subtext="提升显著" icon={Mic} />
                    <StatCard title="高频薄弱点" value="虚拟式" subtext="建议强化" icon={AlertCircle} trend="警示" />
                    <StatCard title="跨文化理解" value="A+" subtext="表现优异" icon={Globe} />
                </div>
            </div>

            {/* 学生列表 */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                    <h2 className="text-lg font-bold text-gray-800">学生个性化分析列表</h2>
                    <button className="text-indigo-600 text-sm font-medium hover:underline border border-indigo-200 px-3 py-1 rounded-lg hover:bg-indigo-50 transition-colors">
                        导出全班报告
                    </button>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-50 text-left">
                        <tr>
                            <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">学生信息</th>
                            <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">核心弱点</th>
                            <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">AI 推荐路径</th>
                            <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">状态</th>
                            <th className="px-6 py-4 text-right">操作</th>
                        </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                        {students.map((student) => (
                            <tr key={student.id} className="hover:bg-indigo-50/30 transition-colors group">
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-3">
                                        <div className="w-9 h-9 bg-gray-100 rounded-full flex items-center justify-center text-gray-600 font-bold text-sm group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                                            {student.name[0]}
                                        </div>
                                        <div>
                                            <div className="font-medium text-gray-800">{student.name}</div>
                                            <div className="text-xs text-gray-400">{student.uid}</div>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-50 text-red-600">
                      {student.weak}
                    </span>
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-600">{student.path}</td>
                                <td className="px-6 py-4">
                     <span className={`text-xs font-medium px-2 py-1 rounded-lg ${student.status === '已完成' ? 'bg-green-100 text-green-700' : 'bg-blue-50 text-blue-600'}`}>
                       {student.status}
                     </span>
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <button
                                        onClick={() => navigate(`/teacher/student/${student.id}`, { state: { student } })}
                                        className="text-indigo-600 hover:text-indigo-800 text-sm font-medium flex items-center justify-end gap-1 ml-auto"
                                    >
                                        <BarChart3 size={16} /> 画像
                                    </button>
                                </td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default TeacherDashboard;