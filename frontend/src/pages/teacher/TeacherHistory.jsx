import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LayoutDashboard, LogOut, RefreshCw, FileText, ArrowLeft, Eye, MessageSquare, AlertCircle } from 'lucide-react';
import request from '../../api/request';
import { API_TEACHER_SCENARIO_LIST, API_TEACHER_EXAM_LIST, API_TEACHER_EXAM_DETAIL } from '../../api/config';

const TeacherHistory = () => {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('scenarios');
    const [scenarios, setScenarios] = useState([]);
    const [exams, setExams] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Modal state for exam details
    const [modalOpen, setModalOpen] = useState(false);
    const [currentExamContent, setCurrentExamContent] = useState(null);
    const [examLoading, setExamLoading] = useState(false);

    useEffect(() => {
        fetchHistoryList(activeTab);
    }, [activeTab]);

    const fetchHistoryList = async (tab) => {
        setLoading(true);
        setError(null);
        try {
            if (tab === 'scenarios') {
                const res = await request.get(API_TEACHER_SCENARIO_LIST);
                if (res.data.code === 200) {
                    setScenarios(res.data.data);
                } else {
                    setError(res.data.message || '获取情景任务记录失败');
                }
            } else if (tab === 'exams') {
                const res = await request.get(API_TEACHER_EXAM_LIST);
                if (res.data.code === 200) {
                    setExams(res.data.data);
                } else {
                    setError(res.data.message || '获取试卷记录失败');
                }
            }
        } catch (err) {
            console.error('获取历史记录错误:', err);
            setError(err.response?.data?.message || err.message || '网路请求错误');
        } finally {
            setLoading(false);
        }
    };

    const handleViewExam = async (examId) => {
        setModalOpen(true);
        setExamLoading(true);
        setCurrentExamContent(null);
        setError(null);

        try {
            const res = await request.get(`${API_TEACHER_EXAM_DETAIL}/${examId}`);
            if (res.data.code === 200) {
                setCurrentExamContent(res.data.data);
            } else {
                setError(res.data.message || '获取试卷详情失败');
            }
        } catch (err) {
            console.error('获取试卷详情错误:', err);
            setError(err.response?.data?.message || err.message || '获取详情失败');
        } finally {
            setExamLoading(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('authToken');
        localStorage.removeItem('userInfo');
        navigate('/');
    };

    // Format ISO date to local string
    const formatDate = (dateString) => {
        if (!dateString) return '-';
        const d = new Date(dateString);
        return d.toLocaleString('zh-CN', {
            year: 'numeric', month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit'
        });
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col items-center py-8">
            <div className="w-full max-w-6xl px-4 flex flex-col gap-6">

                {/* 1. 顶部 Header 区 */}
                <div className="flex justify-between items-center w-full">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => navigate('/teacher/dashboard')}
                            className="bg-white dark:bg-gray-800 p-2.5 rounded-full shadow hover:bg-gray-100 dark:hover:bg-gray-700 transition"
                            title="返回控制台"
                        >
                            <ArrowLeft size={20} className="text-gray-600 dark:text-gray-400" />
                        </button>
                        <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-200 flex items-center gap-3">
                            <FileText size={32} className="text-indigo-600 dark:text-indigo-400" />
                            发布历史记录
                        </h1>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={() => fetchHistoryList(activeTab)}
                            disabled={loading}
                            className="bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700 px-4 py-2.5 rounded-xl font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-all flex items-center gap-2 disabled:opacity-50"
                        >
                            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> 刷新
                        </button>
                        <button
                            onClick={handleLogout}
                            className="bg-white dark:bg-gray-800 text-red-500 border border-red-100 dark:border-red-900/50 px-4 py-2.5 rounded-xl font-medium hover:bg-red-50 dark:hover:bg-red-900/40 transition-all flex items-center gap-2"
                        >
                            <LogOut size={16} /> 退出
                        </button>
                    </div>
                </div>

                {/* 错误提示 */}
                {error && (
                    <div className="bg-red-50 dark:bg-red-900/30 text-red-600 px-4 py-3 rounded-xl flex items-center gap-2 border border-red-100">
                        <AlertCircle size={18} /> {error}
                    </div>
                )}

                {/* 2. 内容区区 (白底卡片) */}
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm dark:shadow-gray-900/50 border border-gray-200 dark:border-gray-700 overflow-hidden flex flex-col min-h-[600px]">

                    {/* Tabs */}
                    <div className="flex border-b border-gray-200 dark:border-gray-700">
                        <button
                            className={`flex-1 py-4 font-bold text-lg flex justify-center items-center gap-2 transition-colors ${activeTab === 'scenarios' ? 'bg-indigo-50 dark:bg-indigo-900/30 border-b-2 border-indigo-600 text-indigo-700 dark:text-indigo-400' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
                            onClick={() => setActiveTab('scenarios')}
                        >
                            <MessageSquare size={20} /> 情景任务记录
                        </button>
                        <button
                            className={`flex-1 py-4 font-bold text-lg flex justify-center items-center gap-2 transition-colors ${activeTab === 'exams' ? 'bg-indigo-50 dark:bg-indigo-900/30 border-b-2 border-indigo-600 text-indigo-700 dark:text-indigo-400' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
                            onClick={() => setActiveTab('exams')}
                        >
                            <FileText size={20} /> 试卷生成记录
                        </button>
                    </div>

                    {/* Table View */}
                    <div className="p-6 flex-1 overflow-auto">
                        {loading && !modalOpen ? (
                            <div className="flex justify-center items-center h-full text-indigo-500">
                                <RefreshCw className="animate-spin mr-2" size={24} /> 加载数据中...
                            </div>
                        ) : activeTab === 'scenarios' ? (
                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse">
                                    <thead>
                                        <tr className="bg-gray-50 dark:bg-gray-900 text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
                                            <th className="p-4 font-medium rounded-tl-lg">任务编号</th>
                                            <th className="p-4 font-medium text-gray-700 dark:text-gray-300">主题</th>
                                            <th className="p-4 font-medium text-gray-700 dark:text-gray-300">难度设定</th>
                                            <th className="p-4 font-medium text-gray-700 dark:text-gray-300">AI人设</th>
                                            <th className="p-4 font-medium rounded-tr-lg">发布时间</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                                        {scenarios.length === 0 ? (
                                            <tr><td colSpan="5" className="p-8 text-center text-gray-400 dark:text-gray-500">暂无情景任务发布记录</td></tr>
                                        ) : (
                                            scenarios.map(item => (
                                                <tr key={item.id} className="hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-colors cursor-pointer group">
                                                    <td className="p-4 text-sm font-mono text-gray-500 dark:text-gray-400">{item.code}</td>
                                                    <td className="p-4 font-medium text-gray-800 dark:text-gray-200">{item.theme}</td>
                                                    <td className="p-4 text-sm">
                                                        <span className="bg-indigo-100 text-indigo-700 dark:text-indigo-400 px-2 py-1 rounded-md text-xs font-bold">{item.difficulty}</span>
                                                    </td>
                                                    <td className="p-4 text-sm text-gray-600 dark:text-gray-400">{item.persona}</td>
                                                    <td className="p-4 text-sm text-gray-500 dark:text-gray-400">{formatDate(item.createdAt)}</td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse">
                                    <thead>
                                        <tr className="bg-gray-50 dark:bg-gray-900 text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
                                            <th className="p-4 font-medium rounded-tl-lg">试卷编号</th>
                                            <th className="p-4 font-medium">语法题数</th>
                                            <th className="p-4 font-medium">阅读题数</th>
                                            <th className="p-4 font-medium">出题策略</th>
                                            <th className="p-4 font-medium">生成时间</th>
                                            <th className="p-4 font-medium text-center rounded-tr-lg">操作</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                                        {exams.length === 0 ? (
                                            <tr><td colSpan="6" className="p-8 text-center text-gray-400 dark:text-gray-500">暂无试卷生成记录</td></tr>
                                        ) : (
                                            exams.map(item => (
                                                <tr key={item.id} className="hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-colors cursor-pointer group">
                                                    <td className="p-4 text-sm font-mono text-gray-500 dark:text-gray-400">{item.code}</td>
                                                    <td className="p-4 text-gray-800 dark:text-gray-200">{item.grammarItems}道</td>
                                                    <td className="p-4 text-gray-800 dark:text-gray-200">{item.writingItems}道</td>
                                                    <td className="p-4 text-sm text-gray-600 dark:text-gray-400">
                                                        {item.strategy === 'personalized' ? '智能个性化' : '默认题海'}
                                                    </td>
                                                    <td className="p-4 text-sm text-gray-500 dark:text-gray-400">{formatDate(item.createdAt)}</td>
                                                    <td className="p-4 text-center">
                                                        <button
                                                            onClick={() => handleViewExam(item.id)}
                                                            className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 bg-indigo-50 dark:bg-indigo-900/30 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-1 mx-auto"
                                                        >
                                                            <Eye size={16} /> 查看
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* 查看详情 Modal */}
            {modalOpen && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex justify-center items-center px-4">
                    <div className="bg-white dark:bg-gray-800 w-full max-w-4xl rounded-2xl shadow-xl flex flex-col max-h-[90vh]">
                        <div className="p-6 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-900 rounded-t-2xl">
                            <h2 className="text-xl font-bold text-gray-800 dark:text-gray-200 flex items-center gap-2">
                                <FileText className="text-indigo-600 dark:text-indigo-400" />
                                试卷内容预览
                            </h2>
                            <button
                                onClick={() => setModalOpen(false)}
                                className="text-gray-400 dark:text-gray-500 hover:text-gray-800 dark:text-gray-200 transition-colors p-1"
                            >
                                ✕
                            </button>
                        </div>

                        <div className="p-6 flex-1 overflow-auto bg-gray-900 text-gray-300 relative">
                            {examLoading ? (
                                <div className="flex justify-center items-center h-48 text-indigo-400">
                                    <RefreshCw className="animate-spin mr-2" size={24} /> 解析试卷数据中...
                                </div>
                            ) : currentExamContent ? (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 p-2">
                                    {Object.entries(currentExamContent).map(([key, value]) => {
                                        if (key === '题目列表' && Array.isArray(value)) {
                                            return (
                                                <div key={key} className="col-span-1 md:col-span-2 space-y-4 mt-6">
                                                    <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 border-l-4 border-indigo-600 pl-3">具体题目清单</h3>
                                                    <div className="grid grid-cols-1 gap-4">
                                                        {value.map((q, idx) => (
                                                            <div key={q.id || idx} className="bg-white dark:bg-gray-700/50 p-5 rounded-2xl border border-gray-100 dark:border-gray-600 shadow-sm hover:shadow-md transition-shadow">
                                                                <div className="flex justify-between items-center mb-3">
                                                                    <div className="flex gap-2">
                                                                        <span className={`text-[10px] uppercase font-black px-2 py-0.5 rounded-full ${q.type === 'grammar' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300' : 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300'}`}>
                                                                            {q.type === 'grammar' ? 'Grammatik' : 'Schreiben'}
                                                                        </span>
                                                                        <span className="text-[10px] font-bold bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 px-2 py-0.5 rounded-full">ID: {q.id}</span>
                                                                    </div>
                                                                    <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400">{q.score} 分</span>
                                                                </div>
                                                                <p className="text-sm font-bold text-gray-800 dark:text-gray-100 mb-3">{q.instruction}</p>
                                                                <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-xl text-sm leading-relaxed text-gray-700 dark:text-gray-300 border-l-3 border-indigo-200 dark:border-indigo-800 font-medium mb-3">
                                                                    {q.content}
                                                                </div>
                                                                {q.options && (
                                                                    <div className="grid grid-cols-2 gap-2">
                                                                        {q.options.map(opt => {
                                                                            const isCorrect = q.answer && (opt.startsWith(q.answer + '.') || opt.startsWith(q.answer + ' ') || opt === q.answer || q.answer.startsWith(opt) || opt.startsWith(q.answer));
                                                                            return (
                                                                                <div key={opt} className={`text-xs p-2 border rounded-lg font-medium ${isCorrect ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-700 dark:text-green-400' : 'bg-gray-50 dark:bg-gray-800/40 border-gray-100 dark:border-gray-700 text-gray-500 dark:text-gray-400'}`}>
                                                                                    {opt}
                                                                                </div>
                                                                            )
                                                                        })}
                                                                    </div>
                                                                )}
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            );
                                        }
                                        return (
                                            <div key={key} className="bg-indigo-50 dark:bg-indigo-900/30 p-4 rounded-xl flex flex-col gap-1 border border-indigo-100 dark:border-indigo-800/50">
                                                <span className="text-gray-500 dark:text-gray-400 font-medium">{key}</span>
                                                <span className="font-semibold text-indigo-800 dark:text-indigo-300 text-base">
                                                    {Array.isArray(value) ? (value.length > 0 ? value.join('、 ') : '全部/无特定') : value}
                                                </span>
                                            </div>
                                        );
                                    })}
                                </div>
                            ) : (
                                <div className="flex justify-center items-center h-48 text-gray-500 dark:text-gray-400">
                                    无法加载试卷内容，可能该试卷格式解析失败。
                                </div>
                            )}
                        </div>

                        <div className="p-4 border-t border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 rounded-b-2xl flex justify-end">
                            <button
                                onClick={() => setModalOpen(false)}
                                className="bg-indigo-600 text-white px-6 py-2 rounded-xl font-medium hover:bg-indigo-700 transition"
                            >
                                关闭
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TeacherHistory;
