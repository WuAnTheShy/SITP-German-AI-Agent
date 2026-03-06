import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, XCircle, FileText, MessageSquare, Award } from 'lucide-react';
import request from '../../api/request';

const ExamResult = () => {
    const { userId, assignmentId } = useParams();
    const navigate = useNavigate();

    const [resultData, setResultData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchResult();
    }, [assignmentId]);

    const fetchResult = async () => {
        setLoading(true);
        try {
            const res = await request.get(`/api/student/exam/result/${assignmentId}`);
            if (res.data.code === 200) {
                setResultData(res.data.data);
            } else {
                setError(res.data.message || '获取结果失败');
            }
        } catch (err) {
            console.error(err);
            setError('网络错误，请稍后刷新重试');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex justify-center items-center">
                <div className="text-indigo-600 animate-pulse font-bold">正在加载答卷记录...</div>
            </div>
        );
    }

    if (error || !resultData) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col items-center justify-center p-4">
                <div className="bg-red-50 text-red-600 p-6 rounded-2xl max-w-md text-center">
                    <p className="font-bold mb-4">{error || '数据不存在'}</p>
                    <button
                        onClick={() => navigate(`/student/${userId}/tasks`)}
                        className="bg-white px-4 py-2 rounded-lg border border-red-200 text-sm"
                    >
                        返回任务中心
                    </button>
                </div>
            </div>
        );
    }

    const { exam_code, content, answers, score, ai_comment } = resultData;

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4 flex justify-center">
            <div className="w-full max-w-4xl flex flex-col gap-6">

                {/* Header */}
                <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-4 mb-6">
                        <button
                            onClick={() => navigate(`/student/${userId}/tasks`)}
                            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full text-gray-500 dark:text-gray-400 transition"
                        >
                            <ArrowLeft size={24} />
                        </button>
                        <div className="flex-1">
                            <h1 className="text-xl font-bold text-gray-800 dark:text-gray-200 flex items-center gap-2">
                                <FileText className="text-indigo-600" />
                                {exam_code} 答卷回顾
                            </h1>
                        </div>
                        <div className="text-right">
                            <div className="text-sm font-bold text-gray-400 uppercase tracking-wider">客观题得分</div>
                            <div className="text-3xl font-black text-indigo-600 dark:text-indigo-400">{score}</div>
                        </div>
                    </div>

                    {ai_comment && (
                        <div className="bg-indigo-50 dark:bg-indigo-900/30 p-4 rounded-xl border border-indigo-100 dark:border-indigo-800/50 flex gap-3">
                            <Award className="text-indigo-600 shrink-0" />
                            <div className="text-sm text-indigo-800 dark:text-indigo-200 whitespace-pre-wrap">
                                <span className="font-bold block mb-1">批改建议及详情：</span>
                                {ai_comment}
                            </div>
                        </div>
                    )}
                </div>

                {/* Questions Review */}
                <div className="space-y-6 mb-12">
                    {content.map((q, idx) => {
                        const isGrammar = q.type === 'grammar';
                        const studentAnswer = answers[idx] || '未作答';
                        const correctAnswer = q.answer;

                        // Robust match for objective questions
                        let isCorrect = false;
                        if (isGrammar && studentAnswer && correctAnswer) {
                            const u = String(studentAnswer).trim();
                            const c = String(correctAnswer).trim();
                            isCorrect = (u === c || u.startsWith(c + '.') || u.startsWith(c + ' ') || c.startsWith(u) || u.startsWith(c));
                        }

                        return (
                            <div key={idx} className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 relative overflow-hidden">
                                <div className={`absolute top-0 left-0 w-1 h-full ${isGrammar ? (isCorrect ? 'bg-green-500' : 'bg-red-500') : 'bg-blue-500'}`}></div>

                                <div className="flex justify-between items-start mb-4">
                                    <div className="flex items-center gap-3">
                                        <span className={`font-bold px-3 py-1 rounded-lg text-sm ${isGrammar
                                                ? (isCorrect ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400')
                                                : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                                            }`}>
                                            Q{idx + 1}. {isGrammar ? '语法题' : '写作题'}
                                        </span>
                                        {isGrammar && (
                                            isCorrect
                                                ? <span className="text-green-600 flex items-center gap-1 text-xs font-bold"><CheckCircle size={14} /> 正确</span>
                                                : <span className="text-red-600 flex items-center gap-1 text-xs font-bold"><XCircle size={14} /> 错误</span>
                                        )}
                                    </div>
                                    <span className="text-xs font-bold text-gray-400">{q.score} 分</span>
                                </div>

                                <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">{q.instruction}</p>
                                <div className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-xl text-sm text-gray-800 dark:text-gray-200 mb-5 border border-gray-100 dark:border-gray-800 font-medium">
                                    {q.content}
                                </div>

                                <div className="space-y-3">
                                    <div className={`p-4 rounded-xl border ${isGrammar ? (isCorrect ? 'bg-green-50/30 border-green-200 dark:border-green-900/50' : 'bg-red-50/30 border-red-200 dark:border-red-900/50') : 'bg-blue-50/30 border-blue-200 dark:border-blue-900/50'}`}>
                                        <div className="text-xs font-bold text-gray-400 mb-2 uppercase tracking-tight">你的回答</div>
                                        <div className="text-sm font-bold text-gray-800 dark:text-gray-200 whitespace-pre-wrap">{studentAnswer}</div>
                                    </div>

                                    {isGrammar && !isCorrect && (
                                        <div className="p-4 rounded-xl bg-green-50/50 border border-green-200 dark:bg-green-900/20 dark:border-green-800/50">
                                            <div className="text-xs font-bold text-green-600 dark:text-green-400 mb-2 uppercase tracking-tight">正确答案</div>
                                            <div className="text-sm font-bold text-green-800 dark:text-green-200">{correctAnswer}</div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

export default ExamResult;
