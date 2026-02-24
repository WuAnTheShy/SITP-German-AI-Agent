import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import request from '../../api/request';
import { MessageSquare, ArrowLeft, CheckCircle, Loader2, Send } from 'lucide-react';
import { API_SCENARIO_PUBLISH } from '../../api/config';
import { useToast } from '../../components/Toast';

const ScenarioLaunch = () => {
    const navigate = useNavigate();
    const toast = useToast();
    const [isProcessing, setIsProcessing] = useState(false);

    // 🟢 1. 状态管理：实时捕获"点击的配置"
    // ----------------------------------------------------------------
    const [selectedTheme, setSelectedTheme] = useState('慕尼黑机场问路'); // 默认选中第一个
    const [difficulty, setDifficulty] = useState('A1 - 入门 (基础词汇)');
    const [persona, setPersona] = useState('友好耐心 (Encouraging)');

    // 训练目标（复选框状态）
    const [goals, setGoals] = useState({
        perfectTense: true,  // 对应 "强制使用完成时态"
        b1Vocab: false       // 对应 "包含至少 5 个 B1 级词汇"
    });

    // 选项数据定义
    const THEMES = ['慕尼黑机场问路', '餐厅点餐 (Bestellung)', '校园迎新 (Campus)'];
    const LEVELS = ['A1 - 入门 (基础词汇)', 'A2 - 初级 (简单从句)', 'B1 - 进阶 (流利交流)'];
    const PERSONAS = ['友好耐心 (Encouraging)', '严谨纠错 (Strict)', '幽默风趣 (Humorous)'];

    // 🟢 2. 发布逻辑：发送收集到的配置
    // ----------------------------------------------------------------
    const handlePublish = async () => {
        setIsProcessing(true);

        // 构造发送给后端的数据包 (Payload)
        const payload = {
            config: {
                theme: selectedTheme,       // 选中的主题
                difficulty: difficulty,     // 选中的难度
                persona: persona,           // 选中的性格
                goals: {                    // 勾选的目标
                    requirePerfectTense: goals.perfectTense,
                    requireB1Vocab: goals.b1Vocab
                }
            },
            timestamp: new Date().toISOString()
        };

        console.log('[Client] 正在发送配置:', payload);

        try {
            const response = await request.post(API_SCENARIO_PUBLISH, payload);

            if (response.data.code === 200) {
                const scenarioId = response.data.data?.scenarioId || 'N/A';
                toast.success(`任务发布成功！ID: ${scenarioId}，主题: ${selectedTheme}`);
                setTimeout(() => navigate('/teacher/dashboard'), 1500);
            } else {
                throw new Error(response.data.message || '发布失败');
            }
        } catch (err) {
            console.error('发布出错:', err);
            const errMsg = err.response?.data?.message || err.message || '网络连接超时';
            toast.error(`发布失败: ${errMsg}`);
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                {/* 顶部导航 */}
                <div className="p-6 border-b border-gray-100 flex items-center gap-4">
                    <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 rounded-lg text-gray-500 transition-colors">
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                            <MessageSquare className="text-purple-600" /> 发布情景模拟任务
                        </h1>
                        <p className="text-sm text-gray-500">配置 AI 陪练角色与场景参数</p>
                    </div>
                </div>

                {/* 核心表单区 */}
                <div className="p-8 space-y-8">
                    {/* 1. 主题选择 (点击卡片切换状态) */}
                    <div>
                        <label className="block text-sm font-bold text-gray-700 mb-3">选择情景主题 (Szenario)</label>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {THEMES.map((theme) => (
                                <div
                                    key={theme}
                                    onClick={() => setSelectedTheme(theme)}
                                    className={`relative group cursor-pointer border-2 rounded-xl p-4 text-center transition-all ${selectedTheme === theme
                                        ? 'border-purple-600 bg-purple-50 text-purple-700'
                                        : 'border-gray-200 hover:border-purple-200 text-gray-700'
                                        }`}
                                >
                                    <div className="font-medium">{theme}</div>
                                    {selectedTheme === theme && (
                                        <div className="absolute top-2 right-2 text-purple-600 animate-in zoom-in duration-200">
                                            <CheckCircle size={16} />
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* 2. 难度等级 (Select 变更状态) */}
                        <div>
                            <label className="block text-sm font-bold text-gray-700 mb-2">难度等级 (Niveau)</label>
                            <select
                                value={difficulty}
                                onChange={(e) => setDifficulty(e.target.value)}
                                className="w-full border border-gray-200 rounded-xl p-3 bg-gray-50 focus:bg-white focus:ring-2 focus:ring-purple-500 outline-none transition-all cursor-pointer"
                            >
                                {LEVELS.map(level => <option key={level} value={level}>{level}</option>)}
                            </select>
                        </div>

                        {/* 3. AI 性格 (Select 变更状态) */}
                        <div>
                            <label className="block text-sm font-bold text-gray-700 mb-2">AI 角色性格</label>
                            <select
                                value={persona}
                                onChange={(e) => setPersona(e.target.value)}
                                className="w-full border border-gray-200 rounded-xl p-3 bg-gray-50 focus:bg-white focus:ring-2 focus:ring-purple-500 outline-none transition-all cursor-pointer"
                            >
                                {PERSONAS.map(p => <option key={p} value={p}>{p}</option>)}
                            </select>
                        </div>
                    </div>

                    {/* 4. 训练目标 (Checkbox 变更状态) */}
                    <div className="bg-purple-50 p-6 rounded-xl border border-purple-100">
                        <label className="block text-sm font-bold text-purple-900 mb-3">训练目标设定</label>
                        <div className="space-y-3">
                            <label className="flex items-center gap-3 bg-white p-3 rounded-lg border border-purple-100 cursor-pointer hover:shadow-sm transition-shadow select-none">
                                <input
                                    type="checkbox"
                                    checked={goals.perfectTense}
                                    onChange={(e) => setGoals({ ...goals, perfectTense: e.target.checked })}
                                    className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500"
                                />
                                <span className="text-sm text-gray-700">强制使用完成时态 (Perfekt)</span>
                            </label>
                            <label className="flex items-center gap-3 bg-white p-3 rounded-lg border border-purple-100 cursor-pointer hover:shadow-sm transition-shadow select-none">
                                <input
                                    type="checkbox"
                                    checked={goals.b1Vocab}
                                    onChange={(e) => setGoals({ ...goals, b1Vocab: e.target.checked })}
                                    className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500"
                                />
                                <span className="text-sm text-gray-700">包含至少 5 个 B1 级词汇</span>
                            </label>
                        </div>
                    </div>
                </div>

                {/* 底部按钮 */}
                <div className="p-6 border-t border-gray-100 bg-gray-50 flex justify-end gap-3">
                    <button
                        onClick={() => navigate(-1)}
                        disabled={isProcessing}
                        className="px-6 py-2.5 text-gray-500 hover:bg-gray-200 rounded-xl font-medium transition-colors disabled:opacity-50"
                    >
                        取消
                    </button>
                    <button
                        onClick={handlePublish}
                        disabled={isProcessing}
                        className="px-8 py-2.5 bg-purple-600 text-white rounded-xl font-bold hover:bg-purple-700 hover:shadow-lg hover:-translate-y-0.5 transition-all flex items-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
                    >
                        {isProcessing ? (
                            <><Loader2 size={20} className="animate-spin" /> 发布中...</>
                        ) : (
                            <><Send size={20} /> 确认发布任务</>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ScenarioLaunch;