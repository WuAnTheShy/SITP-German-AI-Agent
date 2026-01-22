import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios'; // 引入 axios
import {
    ArrowLeft, Brain, CheckCircle, BarChart3,
    Mail, MessageCircle, FileText, Clock, AlertCircle,
    X, Play, Mic, Check, Download, FileAudio, FileType, Loader2, PenTool
} from 'lucide-react';

// ----------------------------------------------------------------------
// 🔧 配置区域
// ----------------------------------------------------------------------
// 请替换为您自己的 Apifox 云端 Mock 地址
const MOCK_SERVER_BASE = 'https://m1.apifoxmock.com/m1/7746497-7491372-default';
const API_HOMEWORK_DETAIL = `${MOCK_SERVER_BASE}/api/homework/detail`;

// ----------------------------------------------------------------------
// 📡 API 请求函数
// ----------------------------------------------------------------------
const fetchHomeworkContent = async (homeworkId) => {
    console.log(`[Client] 正在请求作业详情 ID: ${homeworkId}...`);
    try {
        // 发起 GET 请求，携带 id 参数
        const response = await axios.get(API_HOMEWORK_DETAIL, {
            params: { id: homeworkId }
        });

        // 假设 Apifox 返回结构为 { code: 200, data: { ... } }
        if (response.data.code === 200) {
            console.log("[Client] 获取成功:", response.data.data);
            return response.data.data;
        } else {
            throw new Error(response.data.message || '获取失败');
        }
    } catch (err) {
        console.error("[Client] 请求出错:", err);
        // 返回一个兜底的错误对象，防止页面崩溃
        return null;
    }
};

// ----------------------------------------------------------------------
// 🧩 组件：作业详情模态框 (异步加载)
// ----------------------------------------------------------------------
const HomeworkModal = ({ isOpen, onClose, homework }) => {
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState(null); // 存储从 API 拿到的详情数据
    const [error, setError] = useState('');

    // 监听打开动作，加载数据
    useEffect(() => {
        if (isOpen && homework) {
            setLoading(true);
            setError('');
            setData(null);

            // 调用接口
            fetchHomeworkContent(homework.id)
                .then(result => {
                    if (result) {
                        setData(result);
                    } else {
                        setError('无法获取作业内容，请检查网络或接口配置。');
                    }
                })
                .finally(() => {
                    setLoading(false);
                });
        }
    }, [isOpen, homework]);

    if (!isOpen || !homework) return null;

    // 根据 API 返回的 type 字段判断是音频还是文本
    // 如果 API 还没返回数据，先假定类型以防止渲染闪烁，或者等 loading 结束
    const isAudio = data?.type === 'audio';

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl flex flex-col max-h-[90vh]">

                {/* Header */}
                <div className="p-6 border-b border-gray-100 flex justify-between items-start">
                    <div>
                        <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                            {/* 根据 homework.title 或加载后的 type 显示图标 */}
                            <FileText className="text-indigo-600" />
                            {homework.title}
                        </h3>
                        <div className="flex gap-3 text-sm text-gray-500 mt-1">
                            <span className="flex items-center gap-1"><Clock size={14} /> 提交于: {homework.date}</span>
                            <span className={`font-bold ${homework.score >= 90 ? 'text-green-600' : 'text-blue-600'}`}>
                {homework.score ? `${homework.score} 分` : '评分中'}
              </span>
                        </div>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1 hover:bg-gray-100 rounded-lg">
                        <X size={24} />
                    </button>
                </div>

                {/* Content Area */}
                <div className="p-6 overflow-y-auto custom-scrollbar flex-1">

                    {/* 1. Loading 状态 */}
                    {loading && (
                        <div className="flex flex-col items-center justify-center py-12 space-y-4">
                            <Loader2 size={40} className="text-indigo-600 animate-spin" />
                            <p className="text-sm text-gray-500">正在从服务器获取文件内容...</p>
                        </div>
                    )}

                    {/* 2. Error 状态 */}
                    {!loading && error && (
                        <div className="flex flex-col items-center justify-center py-8 text-red-500 bg-red-50 rounded-xl">
                            <AlertCircle size={32} className="mb-2" />
                            <p>{error}</p>
                        </div>
                    )}

                    {/* 3. 成功展示数据 */}
                    {!loading && data && (
                        <div className="space-y-6 animate-in slide-in-from-bottom-2 duration-300">

                            {/* A. 源文件卡片 (File Meta) */}
                            <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className={`p-3 rounded-lg ${isAudio ? 'bg-purple-100 text-purple-600' : 'bg-blue-100 text-blue-600'}`}>
                                        {isAudio ? <FileAudio size={24} /> : <FileType size={24} />}
                                    </div>
                                    <div>
                                        <div className="font-bold text-gray-800 text-sm">{data.meta?.fileName || '未命名文件'}</div>
                                        <div className="text-xs text-gray-500 flex gap-2">
                                            <span>{data.meta?.fileSize}</span>
                                            <span>•</span>
                                            <span>{data.meta?.uploadTime}</span>
                                        </div>
                                    </div>
                                </div>
                                <button className="text-indigo-600 hover:bg-indigo-50 p-2 rounded-lg transition-colors" title="下载源文件">
                                    <Download size={20} />
                                </button>
                            </div>

                            {/* B. 具体内容展示 */}

                            {/* ---> 情况 1: 音频内容 (Audio) */}
                            {isAudio && (
                                <div className="space-y-4">
                                    {/* 波形播放器 */}
                                    <div className="bg-gray-900 rounded-xl p-4 flex items-center gap-4 shadow-inner">
                                        <button className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center text-white hover:bg-purple-500 transition-colors shadow-lg shadow-purple-900/50">
                                            <Play size={20} className="ml-1" />
                                        </button>
                                        <div className="flex-1 h-12 flex items-center gap-1 opacity-80">
                                            {[...Array(30)].map((_, i) => (
                                                <div key={i} className="w-1 bg-purple-400 rounded-full animate-pulse" style={{ height: `${Math.random() * 100}%`, animationDelay: `${i * 0.05}s` }} />
                                            ))}
                                        </div>
                                        <span className="text-xs text-gray-400 font-mono">{data.meta?.duration}</span>
                                    </div>

                                    {/* 逐句分析 */}
                                    <div className="border border-gray-100 rounded-xl p-4">
                                        <h4 className="text-sm font-bold text-gray-700 mb-3">AI 语音识别与诊断</h4>
                                        <div className="space-y-3">
                                            {data.content?.timeline?.map((item, idx) => (
                                                <div key={idx} className="flex gap-3 text-sm">
                                                    <span className="font-mono text-gray-400 text-xs mt-0.5">{item.time}</span>
                                                    <div className={`flex-1 p-2 rounded-lg border ${
                                                        item.type === 'good' ? 'bg-green-50 border-green-100 text-green-800' :
                                                        item.type === 'warn' ? 'bg-yellow-50 border-yellow-100 text-yellow-800' :
                                                        'bg-red-50 border-red-100 text-red-800'
                                                    }`}>
                                                        {item.msg}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                        <div className="mt-4 pt-4 border-t border-gray-100 text-sm text-gray-500 italic">
                                            "{data.content?.transcript}"
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* ---> 情况 2: 文本/题目内容 (Text) */}
                            {!isAudio && Array.isArray(data.content) && (
                                <div className="space-y-3">
                                    {data.content.map((item, idx) => (
                                        <div key={idx} className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                                            <div className="text-gray-800 font-medium mb-2">{item.q}</div>
                                            <div className="flex items-center gap-3 text-sm">
                                                <span className="text-gray-500">学生作答:</span>
                                                {item.correct ? (
                                                    <span className="text-green-600 font-bold flex items-center gap-1">
                            {item.student} <Check size={16} />
                          </span>
                                                ) : (
                                                     <div className="flex items-center gap-2">
                                                         <span className="text-red-500 line-through decoration-red-300">{item.student}</span>
                                                         <span className="text-green-600 font-bold bg-green-50 px-2 py-0.5 rounded">
                              {item.answer}
                            </span>
                                                     </div>
                                                 )}
                                            </div>
                                            {!item.correct && (
                                                <div className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded border border-red-100 flex gap-2">
                                                    <AlertCircle size={14} className="mt-0.5 shrink-0" />
                                                    {item.analysis}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* C. AI 总评 */}
                            <div className="bg-indigo-50 p-4 rounded-xl border border-indigo-100 flex gap-3">
                                <div className="bg-white p-2 rounded-full h-fit text-indigo-600 shadow-sm shrink-0">
                                    <Brain size={20} />
                                </div>
                                <div>
                                    <h4 className="font-bold text-indigo-900 text-sm mb-1">AI 助教总评</h4>
                                    <p className="text-sm text-indigo-800 leading-relaxed">
                                        {data.aiComment}
                                    </p>
                                </div>
                            </div>

                            {/* D. 教师人工反馈 */}
                            <div>
                                <label className="block text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                                    <PenTool size={16} /> 教师人工反馈
                                </label>
                                <textarea
                                    className="w-full border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-indigo-500 outline-none h-24 resize-none"
                                    placeholder="在此处输入您对该作业的补充指导意见..."
                                    defaultValue={homework.feedback !== '等待提交' ? homework.feedback : ''}
                                ></textarea>
                            </div>

                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-gray-100 bg-gray-50 rounded-b-2xl flex justify-end gap-3">
                    <button onClick={onClose} className="px-4 py-2 text-gray-500 hover:bg-gray-200 rounded-lg transition-colors text-sm font-medium">
                        关闭
                    </button>
                    <button className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium flex items-center gap-2">
                        <CheckCircle size={16} /> 保存反馈
                    </button>
                </div>
            </div>
        </div>
    );
};

// ----------------------------------------------------------------------
// 🚀 主页面组件
// ----------------------------------------------------------------------
const StudentDetail = () => {
    const navigate = useNavigate();
    const { state } = useLocation();
    const [selectedHomework, setSelectedHomework] = useState(null);

    // 获取从列表页传过来的学生数据
    const student = state?.student || {
        name: '演示学生', uid: '000000', weak: '未知', score: 0, active: 0, homeworks: []
    };

    const getScoreColor = (score) => {
        if (!score) return 'text-gray-400';
        if (score >= 90) return 'text-green-600';
        if (score >= 80) return 'text-blue-600';
        if (score >= 60) return 'text-orange-600';
        return 'text-red-600';
    };

    const renderStatus = (status) => {
        const styles = {
            '已完成': 'bg-green-100 text-green-700',
            '待订正': 'bg-orange-100 text-orange-700',
            '未提交': 'bg-red-100 text-red-700',
            '进行中': 'bg-blue-100 text-blue-700',
            '逾期补交': 'bg-gray-100 text-gray-700'
        };
        return <span className={`px-2 py-1 rounded text-xs font-medium ${styles[status] || 'bg-gray-100'}`}>{status}</span>;
    };

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-5xl mx-auto space-y-6">

                {/* 顶部导航 */}
                <button onClick={() => navigate(-1)} className="flex items-center text-gray-500 hover:text-indigo-600 font-medium transition-colors mb-4">
                    <ArrowLeft size={20} className="mr-2" /> 返回仪表盘
                </button>

                {/* 1. 个人信息卡片 */}
                <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 flex flex-col md:flex-row items-center md:items-start gap-8">
                    <div className="w-24 h-24 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600 text-3xl font-bold border-4 border-white shadow-lg">
                        {student.name[0]}
                    </div>
                    <div className="flex-1 text-center md:text-left space-y-2">
                        <h1 className="text-3xl font-bold text-gray-900">{student.name}</h1>
                        <div className="text-gray-500 flex items-center justify-center md:justify-start gap-4">
                            <span>学号: {student.uid}</span><span>•</span><span>软件工程(四)班</span>
                        </div>
                        <div className="flex items-center justify-center md:justify-start gap-3 mt-4">
                            <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-bold">活跃度 {student.active}%</span>
                            <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-bold">综合评分 {student.score}</span>
                        </div>
                    </div>
                    <div className="flex gap-3">
                        <button className="p-3 border rounded-xl hover:bg-gray-50 text-gray-600"><Mail size={20} /></button>
                        <button className="p-3 border rounded-xl hover:bg-gray-50 text-gray-600"><MessageCircle size={20} /></button>
                    </div>
                </div>

                {/* 2. 能力雷达 & AI 诊断 */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="md:col-span-2 bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                        <h2 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
                            <BarChart3 className="text-indigo-600" /> 德语能力模型
                        </h2>
                        <div className="space-y-6">
                            {[
                                { label: '听力 (Hören)', val: 80, col: 'bg-blue-500' },
                                { label: '口语 (Sprechen)', val: 65, col: 'bg-orange-500' },
                                { label: '阅读 (Lesen)', val: 90, col: 'bg-green-500' },
                                { label: '写作 (Schreiben)', val: 75, col: 'bg-purple-500' }
                            ].map(skill => (
                                <div key={skill.label}>
                                    <div className="flex justify-between text-sm mb-2 font-medium text-gray-700"><span>{skill.label}</span><span>{skill.val}/100</span></div>
                                    <div className="h-3 bg-gray-100 rounded-full overflow-hidden"><div className={`h-full ${skill.col}`} style={{ width: `${skill.val}%` }}></div></div>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-2xl p-6 text-white shadow-lg flex flex-col justify-between">
                        <div>
                            <h2 className="text-lg font-bold mb-4 flex items-center gap-2"><Brain size={20} className="text-indigo-200" /> AI 智能诊断</h2>
                            <p className="text-indigo-100 text-sm leading-relaxed mb-6">该生在<strong className="text-white border-b border-white/30">口语产出</strong>方面存在畏难情绪...</p>
                        </div>
                        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                            <button className="w-full bg-white text-indigo-600 py-2 rounded-lg font-bold text-sm hover:bg-indigo-50 transition-colors">一键推送方案</button>
                        </div>
                    </div>
                </div>

                {/* 3. 作业列表 */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                            <FileText className="text-indigo-600" /> 作业完成记录
                        </h2>
                        <div className="text-sm text-gray-500 bg-gray-50 px-3 py-1 rounded-lg">共 {student.homeworks?.length || 0} 项</div>
                    </div>

                    <div className="overflow-hidden border border-gray-200 rounded-xl">
                        <table className="w-full">
                            <thead className="bg-gray-50 border-b border-gray-200">
                            <tr>
                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase">作业标题</th>
                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase">提交日期</th>
                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase">状态</th>
                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase">得分</th>
                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase">操作</th>
                            </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100 bg-white">
                            {student.homeworks && student.homeworks.length > 0 ? (
                                student.homeworks.map((hw) => (
                                    <tr key={hw.id} className="hover:bg-gray-50 transition-colors group">
                                        <td className="px-6 py-4 text-sm font-medium text-gray-900 flex items-center gap-2">
                                            {hw.id === 102 ? <Mic size={16} className="text-purple-500"/> : <FileText size={16} className="text-blue-500"/>}
                                            {hw.title}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-500"><span className="flex items-center gap-1"><Clock size={14} /> {hw.date}</span></td>
                                        <td className="px-6 py-4">{renderStatus(hw.status)}</td>
                                        <td className={`px-6 py-4 text-sm font-bold ${getScoreColor(hw.score)}`}>{hw.score ? `${hw.score} 分` : '-'}</td>
                                        <td className="px-6 py-4 text-sm">
                                            <button
                                                onClick={() => setSelectedHomework(hw)}
                                                className="text-indigo-600 hover:text-indigo-800 font-medium hover:underline flex items-center gap-1"
                                            >
                                                查看详情 <ArrowLeft size={14} className="rotate-180" />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                 <tr><td colSpan="5" className="px-6 py-12 text-center text-gray-400">暂无作业记录</td></tr>
                             )}
                            </tbody>
                        </table>
                    </div>
                </div>

            </div>

            {/* 挂载模态框 */}
            <HomeworkModal
                isOpen={!!selectedHomework}
                onClose={() => setSelectedHomework(null)}
                homework={selectedHomework}
            />

        </div>
    );
};

export default StudentDetail;