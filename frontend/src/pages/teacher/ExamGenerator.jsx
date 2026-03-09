import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import request from '../../api/request';
import { FileText, ArrowLeft, Brain, Wand2, MessageSquare, Loader2, Send, Zap } from 'lucide-react';
import { API_EXAM_GENERATE } from '../../api/config';
import { useToast } from '../../components/Toast';

const ExamGenerator = () => {
    const navigate = useNavigate();
    const toast = useToast();
    const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
    const [isProcessing, setIsProcessing] = useState(false);

    // 🟢 1. 状态管理：全量捕获配置
    const [grammarCount, setGrammarCount] = useState(15);
    const [writingCount, setWritingCount] = useState(2);
    const [strategy, setStrategy] = useState('personalized'); // 'personalized' (千人千面) 或 'unified' (统一试卷)

    // 🟢 2. 生成逻辑：发送真实请求
    const handleGenerate = async () => {
        setIsProcessing(true);

        // 构造请求载荷
        const payload = {
            config: {
                grammarItems: Number(grammarCount),
                writingItems: Number(writingCount),
                strategy: strategy, // 核心策略参数
                focusAreas: ['passive_voice', 'subjunctive'] // 基于界面上显示的 AI 建议 (被动语态/虚拟式)
            },
            timestamp: new Date().toISOString()
        };

        console.log('[Client] 正在请求生成试卷:', payload);

        try {
            const response = await request.post(API_EXAM_GENERATE, payload, { timeout: 90000 });

            if (response.data.code === 200) {
                const { examId, studentCount } = response.data.data || {};
                const strategyLabel = strategy === 'personalized' ? '千人千面 (差异化)' : '统一标准';
                toast.success(`试卷生成完毕！ID: ${examId || 'N/A'}，已分发 ${studentCount || 0} 名学生，策略: ${strategyLabel}`);
                setTimeout(() => navigate(`/teacher/${userInfo.id}/dashboard`), 1500);
            } else {
                throw new Error(response.data.message || '生成失败');
            }
        } catch (err) {
            console.error('生成出错:', err);
            const errMsg = err.response?.data?.message || err.message || '网络连接超时';
            toast.error(`生成失败: ${errMsg}`);
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-3 md:p-8">
            <div className="max-w-3xl mx-auto bg-white dark:bg-gray-800 rounded-2xl shadow-sm dark:shadow-gray-900/50 border border-gray-100 dark:border-gray-700 overflow-hidden">
                {/* Header */}
                <div className="p-6 border-b border-gray-100 dark:border-gray-700 flex items-center gap-4">
                    <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-gray-500 dark:text-gray-400 transition-colors">
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <h1 className="text-xl font-bold text-gray-800 dark:text-gray-200 flex items-center gap-2">
                            <Wand2 className="text-blue-600 dark:text-blue-400" /> 智能试卷生成引擎
                        </h1>
                        <p className="text-sm text-gray-500 dark:text-gray-400">基于学情数据的差异化出题系统</p>
                    </div>
                </div>

                <div className="p-4 md:p-8 space-y-6 md:space-y-8">
                    {/* AI 建议 */}
                    <div className="bg-indigo-50 dark:bg-indigo-900/30 p-5 rounded-xl flex gap-4 items-start border border-indigo-100 dark:border-indigo-800/50">
                        <div className="bg-white dark:bg-gray-800 p-2 rounded-lg shadow-sm dark:shadow-gray-900/50 text-indigo-600 dark:text-indigo-400">
                            <Brain size={24} />
                        </div>
                        <div>
                            <h3 className="font-bold text-indigo-900 dark:text-indigo-200 mb-1">AI 诊断建议</h3>
                            <p className="text-sm text-indigo-800 dark:text-indigo-100 leading-relaxed">
                                系统检测到班级近期在 <span className="font-bold border-b-2 border-indigo-300 dark:border-indigo-500">被动语态</span> 和 <span className="font-bold border-b-2 border-indigo-300 dark:border-indigo-500">虚拟式</span> 模块错误率较高（平均错误率 42%）。建议生成专项强化练习。
                            </p>
                        </div>
                    </div>

                    {/* 试卷结构配置 */}
                    <div>
                        <h3 className="text-sm font-bold text-gray-700 dark:text-gray-300 mb-4 uppercase tracking-wider">试卷结构配置</h3>
                        <div className="space-y-4">
                            {/* 语法填空 */}
                            <div className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-blue-300 transition-colors bg-white dark:bg-gray-800 group">
                                <div className="flex items-center gap-4">
                                    <div className="bg-blue-100 p-3 rounded-lg text-blue-600 dark:text-blue-400"><FileText size={20} /></div>
                                    <div>
                                        <div className="font-bold text-gray-800 dark:text-gray-200">语法填空 (Grammatik)</div>
                                        <div className="text-xs text-gray-500 dark:text-gray-400">侧重变格与动词变位</div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 bg-gray-50 dark:bg-gray-900 px-4 py-2 rounded-lg group-hover:bg-blue-50 dark:bg-blue-900/30 transition-colors">
                                    <span className="text-sm font-bold text-gray-700 dark:text-gray-300 w-12 text-right">{grammarCount} 题</span>
                                    <input
                                        type="range" min="5" max="30" step="5"
                                        value={grammarCount}
                                        onChange={(e) => setGrammarCount(e.target.value)}
                                        className="w-32 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600 dark:accent-blue-400"
                                    />
                                </div>
                            </div>

                            {/* 情景改写 */}
                            <div className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-purple-300 transition-colors bg-white dark:bg-gray-800 group">
                                <div className="flex items-center gap-4">
                                    <div className="bg-purple-100 p-3 rounded-lg text-purple-600"><MessageSquare size={20} /></div>
                                    <div>
                                        <div className="font-bold text-gray-800 dark:text-gray-200">情景改写 (Schreiben)</div>
                                        <div className="text-xs text-gray-500 dark:text-gray-400">侧重句子重构能力</div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 bg-gray-50 dark:bg-gray-900 px-4 py-2 rounded-lg group-hover:bg-purple-50 dark:bg-purple-900/30 transition-colors">
                                    <span className="text-sm font-bold text-gray-700 dark:text-gray-300 w-12 text-right">{writingCount} 篇</span>
                                    <input
                                        type="range" min="1" max="5" step="1"
                                        value={writingCount}
                                        onChange={(e) => setWritingCount(e.target.value)}
                                        className="w-32 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-600 dark:accent-purple-400"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* 分发策略 (Radio Group) */}
                    <div>
                        <h3 className="text-sm font-bold text-gray-700 dark:text-gray-300 mb-4 uppercase tracking-wider">分发策略</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* 选项 1: 千人千面 */}
                            <div
                                onClick={() => setStrategy('personalized')}
                                className={`relative border-2 p-5 rounded-xl cursor-pointer flex items-start gap-3 transition-all hover:scale-[1.01] ${strategy === 'personalized' ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/30' : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                                    }`}
                            >
                                <div className={`mt-1 w-4 h-4 rounded-full border flex items-center justify-center ${strategy === 'personalized' ? 'border-blue-600' : 'border-gray-400'
                                    }`}>
                                    {strategy === 'personalized' && <div className="w-2 h-2 rounded-full bg-blue-600" />}
                                </div>
                                <div>
                                    <div className={`font-bold ${strategy === 'personalized' ? 'text-blue-900 dark:text-blue-200' : 'text-gray-700 dark:text-gray-300'}`}>千人千面 (推荐)</div>
                                    <div className={`text-xs mt-1 ${strategy === 'personalized' ? 'text-blue-700 dark:text-blue-300' : 'text-gray-500 dark:text-gray-400'}`}>
                                        AI 根据每位学生的弱点自动替换 30% 的题目，实现精准打击。
                                    </div>
                                </div>
                                {strategy === 'personalized' && (
                                    <div className="absolute top-0 right-0 bg-blue-600 text-white text-[10px] px-2 py-0.5 rounded-bl-lg rounded-tr-lg flex items-center gap-1">
                                        <Zap size={10} fill="white" /> AI 推荐
                                    </div>
                                )}
                            </div>

                            {/* 选项 2: 统一试卷 */}
                            <div
                                onClick={() => setStrategy('unified')}
                                className={`border p-5 rounded-xl cursor-pointer flex items-start gap-3 transition-colors ${strategy === 'unified' ? 'border-gray-600 bg-gray-100 dark:bg-gray-800' : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                                    }`}
                            >
                                <div className={`mt-1 w-4 h-4 rounded-full border flex items-center justify-center ${strategy === 'unified' ? 'border-gray-800' : 'border-gray-400'
                                    }`}>
                                    {strategy === 'unified' && <div className="w-2 h-2 rounded-full bg-gray-800" />}
                                </div>
                                <div>
                                    <div className="font-bold text-gray-700 dark:text-gray-300">统一试卷</div>
                                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">全班使用完全相同的标准试卷，便于横向对比成绩。</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 flex justify-end gap-3">
                    <button
                        onClick={() => navigate(-1)}
                        disabled={isProcessing}
                        className="px-6 py-2.5 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl font-medium transition-colors disabled:opacity-50"
                    >
                        取消
                    </button>
                    <button
                        onClick={handleGenerate}
                        disabled={isProcessing}
                        className="px-8 py-2.5 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 hover:shadow-lg hover:-translate-y-0.5 transition-all flex items-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
                    >
                        {isProcessing ? (
                            <><Loader2 size={20} className="animate-spin" /> 生成中...</>
                        ) : (
                            <><Send size={20} /> 开始生成试卷</>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ExamGenerator;