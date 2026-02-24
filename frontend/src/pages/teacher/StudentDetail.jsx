import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, useParams } from 'react-router-dom';
import request from '../../api/request';
import {
    ArrowLeft, Brain, CheckCircle, BarChart3,
    Mail, MessageCircle, FileText, Clock, AlertCircle,
    X, Download, FileAudio, FileType, Loader2, PenTool,
    GraduationCap, Save, Mic, Send
} from 'lucide-react';
import { API_HOMEWORK_DETAIL, API_HOMEWORK_SAVE, API_STUDENT_DETAIL, API_PUSH_SCHEME } from '../../api/config';
import { useToast } from '../../components/Toast';

// ----------------------------------------------------------------------
// 📡 API 请求函数
// ----------------------------------------------------------------------

// 1. 获取作业详情
const fetchHomeworkContent = async (homeworkId) => {
    try {
        const response = await request.get(API_HOMEWORK_DETAIL, { params: { id: homeworkId } });
        return response.data.code === 200 ? response.data.data : null;
    } catch (err) {
        console.error("请求作业详情失败:", err);
        return null;
    }
};

// 2. 获取学生全局画像
const fetchStudentDetail = async (studentId) => {
    console.log(`[Client] 正在获取学生画像 ID: ${studentId}...`);
    try {
        const response = await request.get(API_STUDENT_DETAIL, { params: { id: studentId } });
        if (response.data.code === 200) {
            return response.data.data;
        } else {
            console.warn(`[Client] 接口返回错误: ${response.data.message}`);
            return null;
        }
    } catch (err) {
        // 捕获 404 等网络错误
        console.warn("[Client] 请求学生信息网络错误:", err.message);
        return null;
    }
};

// ----------------------------------------------------------------------
// 🧩 组件：作业详情模态框
// ----------------------------------------------------------------------
const HomeworkModal = ({ isOpen, onClose, homework, toast }) => {
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState(null);
    const [error, setError] = useState('');
    const [isSaving, setIsSaving] = useState(false);

    // 本地状态：人工评分和反馈
    const [manualScore, setManualScore] = useState('');
    const [manualFeedback, setManualFeedback] = useState('');

    useEffect(() => {
        if (isOpen && homework) {
            setLoading(true);
            setError('');
            setData(null);
            setIsSaving(false);
            setManualScore(homework.score || '');
            setManualFeedback(homework.feedback === '等待提交' ? '' : homework.feedback);

            fetchHomeworkContent(homework.id)
                .then(result => {
                    if (result) {
                        setData(result);
                    } else {
                        setError('无法获取作业内容，请检查网络或接口配置。');
                    }
                })
                .finally(() => setLoading(false));
        }
    }, [isOpen, homework]);

    // 🟢 功能：真实文件下载
    const handleDownload = () => {
        const fileUrl = data?.meta?.fileUrl;
        const fileName = data?.meta?.fileName || 'download_file';

        if (!fileUrl) {
            toast.error('无法下载：后端未返回有效的文件链接');
            return;
        }

        try {
            const link = document.createElement('a');
            link.href = fileUrl;
            link.setAttribute('download', fileName);
            link.target = "_blank";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (err) {
            console.error("下载触发失败:", err);
            toast.error('下载触发失败，请检查浏览器拦截设置');
        }
    };

    // 🟢 功能：保存评分
    const handleSave = async () => {
        if (manualScore === '' || isNaN(Number(manualScore)) || Number(manualScore) < 0 || Number(manualScore) > 100) {
            toast.error('请输入有效的 0-100 分数');
            return;
        }

        setIsSaving(true);
        try {
            const response = await request.post(API_HOMEWORK_SAVE, {
                homeworkId: homework.id,
                score: Number(manualScore),
                feedback: manualFeedback,
                timestamp: new Date().toISOString()
            });

            if (response.data.code === 200) {
                toast.success(`评分保存成功！最终得分: ${manualScore}`);
                onClose();
            } else {
                throw new Error(response.data.message || '后端业务处理失败');
            }
        } catch (err) {
            const errMsg = err.response?.data?.message || err.message || '网络连接超时';
            toast.error(`保存失败: ${errMsg}`);
        } finally {
            setIsSaving(false);
        }
    };

    if (!isOpen || !homework) {
        return null;
    }

    const isAudio = data?.type === 'audio';

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg flex flex-col max-h-[90vh]">
                {/* Header */}
                <div className="p-6 border-b border-gray-100 flex justify-between items-start">
                    <div>
                        <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                            <FileText className="text-indigo-600" />{homework.title}
                        </h3>
                        <div className="flex gap-3 text-sm text-gray-500 mt-1">
                            <span className="flex items-center gap-1"><Clock size={14} /> 提交于: {homework.date}</span>
                        </div>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1 hover:bg-gray-100 rounded-lg"><X size={24} /></button>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto custom-scrollbar flex-1">
                    {loading && (
                        <div className="flex flex-col items-center justify-center py-12 space-y-4">
                            <Loader2 size={40} className="text-indigo-600 animate-spin" />
                            <p className="text-sm text-gray-500">正在获取作业数据...</p>
                        </div>
                    )}

                    {!loading && error && (
                        <div className="flex flex-col items-center justify-center py-8 text-red-500 bg-red-50 rounded-xl">
                            <AlertCircle size={32} className="mb-2" /><p>{error}</p>
                        </div>
                    )}

                    {!loading && data && (
                        <div className="space-y-6 animate-in slide-in-from-bottom-2 duration-300">
                            {/* 文件下载 */}
                            <div className="space-y-2">
                                <label className="text-sm font-bold text-gray-700 flex items-center gap-2">
                                    <Download size={16} /> 作业文件下载
                                </label>
                                <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 flex items-center justify-between hover:border-indigo-200 transition-colors">
                                    <div className="flex items-center gap-3">
                                        <div className={`p-3 rounded-lg ${isAudio ? 'bg-purple-100 text-purple-600' : 'bg-blue-100 text-blue-600'}`}>
                                            {isAudio ? <FileAudio size={24} /> : <FileType size={24} />}
                                        </div>
                                        <div>
                                            <div className="font-bold text-gray-800 text-sm">{data.meta?.fileName || '未命名文件'}</div>
                                            <div className="text-xs text-gray-500 flex gap-2"><span>{data.meta?.fileSize}</span><span>•</span><span>{data.meta?.uploadTime}</span></div>
                                        </div>
                                    </div>
                                    <button onClick={handleDownload} className="text-indigo-600 bg-indigo-50 hover:bg-indigo-100 p-2.5 rounded-lg transition-colors flex items-center gap-2 text-sm font-bold">
                                        <Download size={18} /> 下载
                                    </button>
                                </div>
                            </div>

                            {/* AI 点评 */}
                            <div className="space-y-2">
                                <label className="text-sm font-bold text-gray-700 flex items-center gap-2">
                                    <Brain size={16} className="text-purple-600" /> AI 智能评分
                                </label>
                                <div className="bg-gradient-to-br from-indigo-50 to-purple-50 p-5 rounded-xl border border-indigo-100 relative overflow-hidden">
                                    <div className="flex gap-4">
                                        <div className="bg-white/80 p-2 rounded-lg h-fit text-indigo-600 shadow-sm shrink-0 backdrop-blur-sm"><Brain size={24} /></div>
                                        <div>
                                            <div className="font-bold text-indigo-900 text-sm mb-2 flex items-center justify-between">
                                                <span>AI 助教点评</span>
                                                <span className="bg-white/50 px-2 py-0.5 rounded text-xs text-indigo-700 border border-indigo-100 flex items-center gap-1"><CheckCircle size={10} /> 自动批改完成</span>
                                            </div>
                                            <p className="text-sm text-indigo-800 leading-relaxed text-justify whitespace-pre-wrap">{data.aiComment || "暂无 AI 评价数据。"}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* 人工评分 */}
                            <div className="space-y-3 pt-2 border-t border-gray-100">
                                <div className="flex items-center justify-between">
                                    <label className="text-sm font-bold text-gray-700 flex items-center gap-2"><PenTool size={16} /> 教师人工评分</label>
                                </div>
                                <div className="grid grid-cols-1 gap-4 bg-gray-50 p-4 rounded-xl border border-gray-200">
                                    <div>
                                        <label className="block text-xs font-medium text-gray-500 mb-1.5 uppercase">最终得分 (Points)</label>
                                        <div className="relative">
                                            <input type="number" min="0" max="100" value={manualScore} onChange={(e) => setManualScore(e.target.value)}
                                                className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none font-bold text-gray-800" placeholder="0-100" />
                                            <div className="absolute left-3 top-2.5 text-gray-400"><GraduationCap size={18} /></div>
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-gray-500 mb-1.5 uppercase">指导意见 (Feedback)</label>
                                        <textarea value={manualFeedback} onChange={(e) => setManualFeedback(e.target.value)}
                                            className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:ring-2 focus:ring-indigo-500 outline-none h-32 resize-none" placeholder="请输入..." />
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-gray-100 bg-gray-50 rounded-b-2xl flex justify-end gap-3">
                    <button onClick={onClose} disabled={isSaving} className="px-5 py-2.5 text-gray-500 hover:bg-gray-200 rounded-xl transition-colors text-sm font-medium disabled:opacity-50">取消</button>
                    <button onClick={handleSave} disabled={isSaving} className="px-6 py-2.5 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-all text-sm font-bold flex items-center gap-2 disabled:opacity-70">
                        {isSaving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />} 保存评分
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
    const toast = useToast();
    const { id } = useParams();
    const { state } = useLocation();

    const [loading, setLoading] = useState(true);
    const [studentData, setStudentData] = useState(null);
    const [selectedHomework, setSelectedHomework] = useState(null);
    const [isPushing, setIsPushing] = useState(false);

    useEffect(() => {
        const initData = async () => {
            // 1. 🟢 优化：先使用路由传参(State)的缓存数据渲染界面，实现"秒开"
            if (state?.student) {
                const fallbackData = {
                    info: {
                        name: state.student.name || '加载中...',
                        uid: state.student.uid,
                        class: state.student.class || '软件工程',
                        active: state.student.active || 0,
                        score: state.student.score || 0
                    },
                    ability: { listening: 0, speaking: 0, reading: 0, writing: 0 }, // 初始占位
                    aiDiagnosis: "正在分析最新学情...",
                    homeworks: []
                };
                setStudentData(fallbackData);
            }

            setLoading(true);

            // 1. 尝试从 API 获取数据
            const apiData = await fetchStudentDetail(id);

            if (apiData) {
                setStudentData(apiData);
            } else if (state?.student) {
                // 2. 🟢 降级逻辑：防止 API 失败导致页面崩溃
                console.warn("⚠️ API 请求失败，正在使用本地缓存数据进行降级渲染");

                const fallbackData = {
                    info: {
                        name: state.student.name || '未知学生',
                        uid: state.student.uid || '未知学号',
                        class: state.student.class || '软件工程',
                        active: state.student.active || 0,
                        score: state.student.score || 0
                    },
                    ability: {
                        listening: 60, speaking: 60, reading: 60, writing: 60
                    },
                    aiDiagnosis: "⚠️ 网络连接失败，无法获取实时 AI 诊断数据。请检查后端服务是否正常运行。",
                    homeworks: state.student.homeworks || []
                };
                setStudentData(fallbackData);
            } else {
                setStudentData(null);
            }

            setLoading(false);
        };

        if (id) {
            initData();
        }
    }, [id, state]);

    // 辅助函数
    const getScoreColor = (score) => {
        if (!score) {
            return 'text-gray-400';
        }
        if (score >= 90) {
            return 'text-green-600';
        }
        if (score >= 80) {
            return 'text-blue-600';
        }
        if (score >= 60) {
            return 'text-orange-600';
        }
        return 'text-red-600';
    };

    const renderStatus = (status) => {
        const styles = { '已完成': 'bg-green-100 text-green-700', '待订正': 'bg-orange-100 text-orange-700', '未提交': 'bg-red-100 text-red-700', '进行中': 'bg-blue-100 text-blue-700', '逾期补交': 'bg-gray-100 text-gray-700' };
        return <span className={`px-2 py-1 rounded text-xs font-medium ${styles[status] || 'bg-gray-100'}`}>{status}</span>;
    };

    // 🟢 功能：真实推送个性化方案 (已修改为使用学号 uid)
    const handlePushScheme = async () => {
        setIsPushing(true);
        try {
            const studentUid = studentData?.info?.uid;
            console.log(`[Client] 正在为学生 ${studentUid} 推送方案...`);

            const response = await request.post(API_PUSH_SCHEME, {
                studentId: studentUid,
                name: studentData?.info?.name,
                diagnosis: studentData?.aiDiagnosis,
                timestamp: new Date().toISOString()
            });

            if (response.data.code === 200) {
                toast.success(`推送成功！目标学号：${studentUid}，方案名称：${response.data.data?.schemeName || '个性化强化方案'}`);
            } else {
                throw new Error(response.data.message || '服务响应异常');
            }

        } catch (err) {
            console.error("推送失败:", err);
            const errMsg = err.response?.data?.message || err.message || '网络连接超时';
            toast.error(`推送失败: ${errMsg}`);
        } finally {
            setIsPushing(false);
        }
    };

    if (loading) {
        return <div className="min-h-screen flex items-center justify-center bg-gray-50"><Loader2 size={40} className="text-indigo-600 animate-spin" /></div>;
    }

    if (!studentData) {
        return <div className="min-h-screen flex flex-col items-center justify-center text-gray-500">
            <AlertCircle size={48} className="text-gray-300 mb-4" />
            <p className="mb-4">未找到学生数据，请检查网络或接口配置</p>
            <button onClick={() => navigate(-1)} className="text-indigo-600 font-bold hover:underline">返回上一页</button>
        </div>;
    }

    // 安全解构
    const { info, ability, aiDiagnosis, homeworks } = studentData;

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
                        {info.name ? info.name[0] : '?'}
                    </div>
                    <div className="flex-1 text-center md:text-left space-y-2">
                        <h1 className="text-3xl font-bold text-gray-900">{info.name}</h1>
                        <div className="text-gray-500 flex items-center justify-center md:justify-start gap-4">
                            <span>学号: {info.uid}</span><span>•</span><span>{info.class || '软件工程'}</span>
                        </div>
                        <div className="flex items-center justify-center md:justify-start gap-3 mt-4">
                            <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-bold">活跃度 {info.active}%</span>
                            <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-bold">综合评分 {info.score}</span>
                        </div>
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
                                { label: '听力 (Hören)', val: ability.listening, col: 'bg-blue-500' },
                                { label: '口语 (Sprechen)', val: ability.speaking, col: 'bg-orange-500' },
                                { label: '阅读 (Lesen)', val: ability.reading, col: 'bg-green-500' },
                                { label: '写作 (Schreiben)', val: ability.writing, col: 'bg-purple-500' }
                            ].map(skill => (
                                <div key={skill.label}>
                                    <div className="flex justify-between text-sm mb-2 font-medium text-gray-700"><span>{skill.label}</span><span>{skill.val}/100</span></div>
                                    <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                                        <div className={`h-full ${skill.col}`} style={{ width: `${skill.val}%` }}></div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-2xl p-6 text-white shadow-lg flex flex-col justify-between relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-white opacity-5 rounded-full -mr-16 -mt-16"></div>
                        <div>
                            <h2 className="text-lg font-bold mb-4 flex items-center gap-2"><Brain size={20} className="text-indigo-200" /> AI 智能诊断</h2>
                            <p className="text-indigo-100 text-sm leading-relaxed mb-6 whitespace-pre-wrap">{aiDiagnosis}</p>
                        </div>
                        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                            <button onClick={handlePushScheme} disabled={isPushing} className="w-full bg-white text-indigo-600 py-2.5 rounded-lg font-bold text-sm hover:bg-indigo-50 transition-colors flex items-center justify-center gap-2">
                                {isPushing ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />} 一键推送强化方案
                            </button>
                        </div>
                    </div>
                </div>

                {/* 3. 作业列表 */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                            <FileText className="text-indigo-600" /> 作业完成记录
                        </h2>
                        <div className="text-sm text-gray-500 bg-gray-50 px-3 py-1 rounded-lg">共 {homeworks?.length || 0} 项</div>
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
                                {homeworks && homeworks.length > 0 ? (
                                    homeworks.map((hw) => (
                                        <tr key={hw.id} className="hover:bg-gray-50 transition-colors group">
                                            <td className="px-6 py-4 text-sm font-medium text-gray-900 flex items-center gap-2">
                                                {hw.id === 102 ? <Mic size={16} className="text-purple-500" /> : <FileText size={16} className="text-blue-500" />}
                                                {hw.title}
                                            </td>
                                            <td className="px-6 py-4 text-sm text-gray-500"><span className="flex items-center gap-1"><Clock size={14} /> {hw.date}</span></td>
                                            <td className="px-6 py-4">{renderStatus(hw.status)}</td>
                                            <td className={`px-6 py-4 text-sm font-bold ${getScoreColor(hw.score)}`}>{hw.score ? `${hw.score} 分` : '-'}</td>
                                            <td className="px-6 py-4 text-sm">
                                                <button onClick={() => setSelectedHomework(hw)} className="text-indigo-600 hover:text-indigo-800 font-medium hover:underline flex items-center gap-1">
                                                    查看详情 <ArrowLeft size={14} className="rotate-180" />
                                                </button>
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="5" className="px-6 py-12 text-center text-gray-400">暂无作业记录</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            {/* 挂载模态框 */}
            <HomeworkModal isOpen={!!selectedHomework} onClose={() => setSelectedHomework(null)} homework={selectedHomework} toast={toast} />
        </div>
    );
};

export default StudentDetail;