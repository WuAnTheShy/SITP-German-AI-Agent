import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, FileText, Send, AlertCircle } from 'lucide-react';
import request from '../../api/request';

const TakeExam = () => {
    const { userId, assignmentId } = useParams();
    const navigate = useNavigate();

    const [examData, setExamData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [answers, setAnswers] = useState({}); // { "0": "A. xxx", "1": "Student writing..." }
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null); // { score, message }

    useEffect(() => {
        fetchExam();
    }, [assignmentId]);

    const fetchExam = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await request.get(`/api/student/exam/assignment/${assignmentId}`);
            if (res.data.code === 200) {
                setExamData(res.data.data);
                if (res.data.data.status === 'completed') {
                    setError('该试卷已经完成，无需重复作答。');
                }
            } else {
                setError(res.data.message || '获取试卷失败');
            }
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.message || err.message || '网络错误');
        } finally {
            setLoading(false);
        }
    };

    const handleAnswerChange = (idx, val) => {
        setAnswers(prev => ({ ...prev, [idx]: val }));
    };

    const handleSubmit = async () => {
        if (!examData) return;

        // Optional: validate all answered
        // const totalQs = examData.content.length;
        // if (Object.keys(answers).length < totalQs) {
        //     if (!window.confirm("你还有未作答的题目，确定要交卷吗？")) return;
        // } else {
        //     if (!window.confirm("确认提交试卷吗？")) return;
        // }

        if (!window.confirm("确认提交答卷吗？提交后不可修改。")) return;

        setSubmitting(true);
        try {
            const res = await request.post('/api/student/exam/submit', {
                assignment_id: parseInt(assignmentId),
                answers: answers
            });

            if (res.data.code === 200) {
                setResult(res.data.data);
                window.scrollTo(0, 0);
            } else {
                alert(res.data.message || '交卷失败');
            }
        } catch (err) {
            console.error(err);
            alert(err.response?.data?.message || '交卷发生错误');
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex justify-center items-center">
                <div className="text-indigo-600 flex items-center gap-2 font-bold animate-pulse">
                    正在加载试卷...
                </div>
            </div>
        );
    }

    if (error && !examData) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col items-center justify-center">
                <div className="bg-red-50 text-red-600 p-6 rounded-2xl flex flex-col items-center gap-4 max-w-md text-center">
                    <AlertCircle size={48} />
                    <p className="font-medium text-lg">{error}</p>
                    <button
                        onClick={() => navigate(`/student/${userId}/tasks`)}
                        className="mt-2 bg-red-100 px-6 py-2 rounded-xl text-red-700 hover:bg-red-200 transition"
                    >
                        返回任务中心
                    </button>
                </div>
            </div>
        );
    }

    if (result) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col items-center justify-center p-4">
                <div className="bg-white dark:bg-gray-800 p-8 rounded-3xl shadow-xl flex flex-col items-center max-w-lg w-full text-center border border-gray-100 dark:border-gray-700">
                    <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex justify-center items-center mb-6">
                        <CheckCircle size={40} />
                    </div>
                    <h2 className="text-2xl font-black text-gray-800 dark:text-gray-100 mb-2">交卷成功！</h2>
                    <p className="text-gray-500 dark:text-gray-400 mb-6">主观题部分将会由AI和老师后续进行批改。客观题得分如下：</p>

                    <div className="bg-indigo-50 dark:bg-indigo-900/30 p-6 rounded-2xl w-full mb-8 border border-indigo-100 dark:border-indigo-800/50">
                        <div className="text-sm font-bold text-indigo-400 mb-1 uppercase tracking-wider">客观题得分</div>
                        <div className="text-5xl font-black text-indigo-600 dark:text-indigo-400">{result.score || 0}</div>
                    </div>

                    <button
                        onClick={() => navigate(`/student/${userId}/tasks`)}
                        className="bg-indigo-600 text-white w-full py-3.5 rounded-xl font-bold hover:bg-indigo-700 transition shadow-md shadow-indigo-200 dark:shadow-none"
                    >
                        返回任务中心
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4 flex justify-center">
            <div className="w-full max-w-4xl max-h-full flex flex-col gap-6">

                {/* Header */}
                <div className="flex items-center gap-4 bg-white dark:bg-gray-800 p-4 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700">
                    <button
                        onClick={() => navigate(`/student/${userId}/tasks`)}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full text-gray-500 dark:text-gray-400 transition"
                    >
                        <ArrowLeft size={24} />
                    </button>
                    <div>
                        <h1 className="text-xl font-bold flex items-center gap-2 text-gray-800 dark:text-gray-200">
                            <FileText className="text-indigo-600" />
                            {examData.exam_code}
                        </h1>
                        <span className="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded mt-1 inline-block font-medium">
                            {examData.strategy === 'personalized' ? '量身定制' : '统一标准'}
                        </span>
                    </div>
                </div>

                {error && (
                    <div className="bg-orange-50 border border-orange-200 text-orange-700 px-4 py-3 rounded-xl flex items-center gap-2">
                        <AlertCircle size={18} /> {error}
                    </div>
                )}

                {/* Questions List */}
                <div className="space-y-6">
                    {examData.content && examData.content.map((q, idx) => {
                        const isGrammar = q.type === 'grammar';
                        return (
                            <div key={idx} className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 relative overflow-hidden">
                                <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-indigo-400 to-purple-500"></div>

                                <div className="flex justify-between items-start mb-4">
                                    <div className="flex items-center gap-3">
                                        <span className="bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300 font-bold px-3 py-1 rounded-lg text-sm">
                                            Q{idx + 1}. {isGrammar ? '语法' : '写作'}
                                        </span>
                                    </div>
                                    <span className="text-sm font-bold text-gray-400 dark:text-gray-500">{q.score} 分</span>
                                </div>

                                <p className="text-base font-medium text-gray-800 dark:text-gray-200 mb-3">{q.instruction}</p>

                                <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-xl text-sm leading-relaxed text-gray-700 dark:text-gray-300 border border-gray-100 dark:border-gray-800 mb-5 font-medium">
                                    {q.content}
                                </div>

                                {/* Input Area */}
                                {isGrammar ? (
                                    q.options && q.options.length > 0 ? (
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                            {q.options.map((opt, i) => (
                                                <label
                                                    key={i}
                                                    className={`cursor-pointer border rounded-xl p-4 flex items-center gap-3 transition-colors ${answers[idx] === opt
                                                            ? 'border-indigo-500 bg-indigo-50/50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300 font-bold'
                                                            : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                                                        }`}
                                                >
                                                    <input
                                                        type="radio"
                                                        name={`q_${idx}`}
                                                        value={opt}
                                                        checked={answers[idx] === opt}
                                                        onChange={() => handleAnswerChange(idx, opt)}
                                                        className="w-4 h-4 text-indigo-600 focus:ring-indigo-500"
                                                    />
                                                    <span className="text-sm">{opt}</span>
                                                </label>
                                            ))}
                                        </div>
                                    ) : (
                                        <input
                                            type="text"
                                            value={answers[idx] || ''}
                                            onChange={(e) => handleAnswerChange(idx, e.target.value)}
                                            placeholder="请输入你的答案..."
                                            className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-xl p-4 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none"
                                        />
                                    )
                                ) : (
                                    <textarea
                                        value={answers[idx] || ''}
                                        onChange={(e) => handleAnswerChange(idx, e.target.value)}
                                        placeholder="请在此输入你的作文..."
                                        className="w-full h-48 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-xl p-4 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none resize-none"
                                    />
                                )}
                            </div>
                        );
                    })}
                </div>

                {/* Submit button */}
                {!error && examData && examData.content && (
                    <div className="mt-8 mb-12 flex justify-end">
                        <button
                            disabled={submitting}
                            onClick={handleSubmit}
                            className={`bg-indigo-600 text-white px-8 py-4 rounded-xl font-bold flex items-center gap-2 shadow-lg shadow-indigo-200 dark:shadow-none transition ${submitting ? 'opacity-70 cursor-not-allowed' : 'hover:bg-indigo-700 hover:-translate-y-0.5'}`}
                        >
                            {submitting ? '正在提交...' : '确认交卷'}
                            {!submitting && <Send size={20} />}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default TakeExam;
