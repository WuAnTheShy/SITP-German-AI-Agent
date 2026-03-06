import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import request from '../../api/request';
import { ArrowLeft, CheckCircle, Clock, FileText, MessageSquare, Play, RotateCw } from 'lucide-react';

const TaskCenter = () => {
    const navigate = useNavigate();
    const { userId } = useParams();
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('pending'); // 'pending' | 'completed'

    useEffect(() => {
        fetchTasks();
    }, []);

    const fetchTasks = async () => {
        setLoading(true);
        try {
            const res = await request.get('/api/student/tasks');
            if (res.data.code === 200) {
                setTasks(res.data.data);
            }
        } catch (error) {
            console.error("获取任务失败:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCompleteScenario = async (taskId) => {
        try {
            await request.post('/api/student/task/complete', {
                task_type: 'scenario',
                task_id: taskId
            });
            fetchTasks();
        } catch (err) {
            console.error("标记完成失败", err);
        }
    };

    const pendingTasks = tasks.filter(t => t.status === 'pending');
    const completedTasks = tasks.filter(t => t.status === 'completed');

    const renderTaskCard = (task) => {
        const isCompleted = task.status === 'completed';
        const isExam = task.type === 'exam';

        return (
            <div key={task.id} className={`p-5 rounded-2xl border ${isCompleted ? 'bg-gray-50 border-gray-200 dark:bg-gray-800/50 dark:border-gray-700' : 'bg-white border-indigo-100 dark:bg-gray-800 dark:border-indigo-900/30'} shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group`}>
                <div className="flex justify-between items-start mb-3">
                    <div className="flex gap-3 items-center">
                        <div className={`p-2.5 rounded-xl ${isExam ? 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' : 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400'}`}>
                            {isExam ? <FileText size={20} /> : <MessageSquare size={20} />}
                        </div>
                        <div>
                            <h3 className="font-bold text-gray-800 dark:text-gray-200 text-lg line-clamp-1" title={task.title}>{task.title}</h3>
                            <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mt-1">
                                <Clock size={12} />
                                <span>{task.createdAt ? new Date(task.createdAt).toLocaleString() : '最近'}</span>
                            </div>
                        </div>
                    </div>
                    {isCompleted ? (
                        <div className="px-2 py-1 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-xs font-bold rounded-full flex items-center gap-1">
                            <CheckCircle size={12} /> 已完成
                        </div>
                    ) : (
                        <div className="px-2 py-1 bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400 text-xs font-bold rounded-full flex items-center gap-1">
                            待办
                        </div>
                    )}
                </div>

                <div className="mt-4 flex gap-2 justify-end">
                    {isExam && !isCompleted && (
                        <button
                            onClick={() => navigate(`/student/${userId}/take-exam/${task.assignment_id}`)}
                            className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 flex items-center gap-1 transition"
                        >
                            <Play size={16} /> 开始测验
                        </button>
                    )}
                    {isExam && isCompleted && (
                        <button
                            onClick={() => navigate(`/student/${userId}/exam-result/${task.assignment_id}`)}
                            className="bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-200 dark:hover:bg-gray-600 transition"
                        >
                            查看作业记录
                        </button>
                    )}

                    {!isExam && !isCompleted && (
                        <>
                            <button
                                onClick={() => navigate(`/student/${userId}/ai-scene-chat`)}
                                className="bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300 px-4 py-2 rounded-lg text-sm font-medium hover:bg-purple-200 transition"
                            >
                                去聊天大厅
                            </button>
                            <button
                                onClick={() => handleCompleteScenario(task.push_id)}
                                className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 flex items-center gap-1 transition"
                            >
                                <CheckCircle size={16} /> 标记完成
                            </button>
                        </>
                    )}
                </div>
            </div>
        );
    };

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => navigate(`/student/${userId}/home`)}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full text-gray-500 dark:text-gray-400 transition"
                    >
                        <ArrowLeft size={24} />
                    </button>
                    <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">📋 任务中心</h1>
                </div>
                <button
                    onClick={fetchTasks}
                    disabled={loading}
                    className="flex items-center gap-2 px-3 py-1.5 bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 rounded-lg text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                >
                    <RotateCw size={14} className={loading ? 'animate-spin' : ''} /> 刷新
                </button>
            </div>

            {/* Tabs */}
            <div className="flex gap-4 mb-6 border-b border-gray-200 dark:border-gray-700">
                <button
                    onClick={() => setActiveTab('pending')}
                    className={`pb-3 px-2 text-sm font-bold transition-colors border-b-2 ${activeTab === 'pending' ? 'text-indigo-600 border-indigo-600 dark:text-indigo-400 dark:border-indigo-400' : 'text-gray-500 border-transparent hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200'}`}
                >
                    待办任务 ({pendingTasks.length})
                </button>
                <button
                    onClick={() => setActiveTab('completed')}
                    className={`pb-3 px-2 text-sm font-bold transition-colors border-b-2 ${activeTab === 'completed' ? 'text-indigo-600 border-indigo-600 dark:text-indigo-400 dark:border-indigo-400' : 'text-gray-500 border-transparent hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200'}`}
                >
                    已完成 ({completedTasks.length})
                </button>
            </div>

            {/* List */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {loading && tasks.length === 0 ? (
                    <div className="col-span-full py-12 flex justify-center items-center text-indigo-500">
                        <RotateCw className="animate-spin" size={32} />
                    </div>
                ) : (activeTab === 'pending' ? pendingTasks : completedTasks).length === 0 ? (
                    <div className="col-span-full py-12 text-center text-gray-500 dark:text-gray-400 bg-white/50 dark:bg-gray-800/50 rounded-2xl border border-dashed border-gray-300 dark:border-gray-700">
                        当前暂无{activeTab === 'pending' ? '待办' : '已完成'}任务
                    </div>
                ) : (
                    (activeTab === 'pending' ? pendingTasks : completedTasks).map(renderTaskCard)
                )}
            </div>
        </div>
    );
};

export default TaskCenter;
