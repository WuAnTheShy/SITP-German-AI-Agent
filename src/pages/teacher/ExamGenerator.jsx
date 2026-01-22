import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, ArrowLeft, Brain, Wand2, MessageSquare } from 'lucide-react';

const ExamGenerator = () => {
    const navigate = useNavigate();
    const [isProcessing, setIsProcessing] = useState(false);

    // 1. 定义状态来存储滑动条的值
    const [grammarCount, setGrammarCount] = useState(15); // 默认 15 题
    const [writingCount, setWritingCount] = useState(2);  // 默认 2 篇

    const handleGenerate = () => {
        setIsProcessing(true);
        setTimeout(() => {
            // 演示时显示具体的配置参数，增强真实感
            alert(`试卷生成完毕！\n配置参数：语法题 ${grammarCount} 道，写作 ${writingCount} 篇。\n已根据差异化策略分发给学生。`);
            navigate('/teacher/dashboard');
        }, 1500);
    };

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-6 border-b border-gray-100 flex items-center gap-4">
                    <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 rounded-lg text-gray-500">
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                            <Wand2 className="text-blue-600" /> 智能试卷生成引擎
                        </h1>
                        <p className="text-sm text-gray-500">基于学情数据的差异化出题系统</p>
                    </div>
                </div>

                <div className="p-8 space-y-8">
                    {/* AI 建议 */}
                    <div className="bg-indigo-50 p-5 rounded-xl flex gap-4 items-start border border-indigo-100">
                        <div className="bg-white p-2 rounded-lg shadow-sm text-indigo-600">
                            <Brain size={24} />
                        </div>
                        <div>
                            <h3 className="font-bold text-indigo-900 mb-1">AI 诊断建议</h3>
                            <p className="text-sm text-indigo-800 leading-relaxed">
                                系统检测到班级近期在 <span className="font-bold border-b-2 border-indigo-300">被动语态</span> 和 <span className="font-bold border-b-2 border-indigo-300">虚拟式</span> 模块错误率较高（平均错误率 42%）。建议生成专项强化练习。
                            </p>
                        </div>
                    </div>

                    {/* 试卷结构 */}
                    <div>
                        <h3 className="text-sm font-bold text-gray-700 mb-4 uppercase tracking-wider">试卷结构配置</h3>
                        <div className="space-y-4">

                            {/* 语法填空配置卡片 */}
                            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-xl hover:border-blue-300 transition-colors bg-white group">
                                <div className="flex items-center gap-4">
                                    <div className="bg-blue-100 p-3 rounded-lg text-blue-600"><FileText size={20} /></div>
                                    <div>
                                        <div className="font-bold text-gray-800">语法填空 (Grammatik)</div>
                                        <div className="text-xs text-gray-500">侧重变格与动词变位</div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 bg-gray-50 px-4 py-2 rounded-lg group-hover:bg-blue-50 transition-colors">
                                    {/* 2. 绑定状态显示 */}
                                    <span className="text-sm font-bold text-gray-700 w-12 text-right">{grammarCount} 题</span>
                                    {/* 3. 绑定 onChange 事件 */}
                                    <input
                                        type="range"
                                        min="5"
                                        max="30"
                                        step="5"
                                        value={grammarCount}
                                        onChange={(e) => setGrammarCount(e.target.value)}
                                        className="w-32 h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                                    />
                                </div>
                            </div>

                            {/* 情景改写配置卡片 */}
                            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-xl hover:border-purple-300 transition-colors bg-white group">
                                <div className="flex items-center gap-4">
                                    <div className="bg-purple-100 p-3 rounded-lg text-purple-600"><MessageSquare size={20} /></div>
                                    <div>
                                        <div className="font-bold text-gray-800">情景改写 (Schreiben)</div>
                                        <div className="text-xs text-gray-500">侧重句子重构能力</div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 bg-gray-50 px-4 py-2 rounded-lg group-hover:bg-purple-50 transition-colors">
                                    {/* 2. 绑定状态显示 */}
                                    <span className="text-sm font-bold text-gray-700 w-12 text-right">{writingCount} 篇</span>
                                    {/* 3. 绑定 onChange 事件 */}
                                    <input
                                        type="range"
                                        min="1"
                                        max="5"
                                        step="1"
                                        value={writingCount}
                                        onChange={(e) => setWritingCount(e.target.value)}
                                        className="w-32 h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                                    />
                                </div>
                            </div>

                        </div>
                    </div>

                    {/* 分发策略 */}
                    <div>
                        <h3 className="text-sm font-bold text-gray-700 mb-4 uppercase tracking-wider">分发策略</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <label className="relative border-2 border-blue-600 bg-blue-50 p-5 rounded-xl cursor-pointer flex items-start gap-3 transition-transform hover:scale-[1.01]">
                                <input type="radio" name="strategy" defaultChecked className="mt-1 w-4 h-4 text-blue-600 focus:ring-blue-500" />
                                <div>
                                    <div className="font-bold text-blue-900">千人千面 (推荐)</div>
                                    <div className="text-xs text-blue-700 mt-1">AI 根据每位学生的弱点自动替换 30% 的题目，实现精准打击。</div>
                                </div>
                                <div className="absolute top-0 right-0 bg-blue-600 text-white text-[10px] px-2 py-0.5 rounded-bl-lg rounded-tr-lg">AI 推荐</div>
                            </label>
                            <label className="border border-gray-200 p-5 rounded-xl cursor-pointer hover:bg-gray-50 flex items-start gap-3">
                                <input type="radio" name="strategy" className="mt-1 w-4 h-4 text-gray-400 focus:ring-gray-400" />
                                <div>
                                    <div className="font-bold text-gray-700">统一试卷</div>
                                    <div className="text-xs text-gray-500 mt-1">全班使用完全相同的标准试卷，便于横向对比成绩。</div>
                                </div>
                            </label>
                        </div>
                    </div>
                </div>

                <div className="p-6 border-t border-gray-100 bg-gray-50 flex justify-end gap-3">
                    <button onClick={() => navigate(-1)} className="px-6 py-2.5 text-gray-500 hover:bg-gray-200 rounded-xl font-medium transition-colors">取消</button>
                    <button
                        onClick={handleGenerate}
                        disabled={isProcessing}
                        className="px-8 py-2.5 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 hover:shadow-lg hover:-translate-y-0.5 transition-all flex items-center gap-2"
                    >
                        {isProcessing ? '生成中...' : '开始生成试卷'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ExamGenerator;