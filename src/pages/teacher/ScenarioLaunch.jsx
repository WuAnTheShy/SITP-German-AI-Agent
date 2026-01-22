import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageSquare, ArrowLeft, CheckCircle } from 'lucide-react';

const ScenarioLaunch = () => {
    const navigate = useNavigate();
    const [isProcessing, setIsProcessing] = useState(false);

    const handlePublish = () => {
        setIsProcessing(true);
        setTimeout(() => {
            alert('任务发布成功！AI 陪练已就位。');
            navigate('/teacher/dashboard');
        }, 1500);
    };

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                {/* 顶部导航 */}
                <div className="p-6 border-b border-gray-100 flex items-center gap-4">
                    <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 rounded-lg text-gray-500">
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
                    {/* 1. 主题选择 */}
                    <div>
                        <label className="block text-sm font-bold text-gray-700 mb-3">选择情景主题 (Szenario)</label>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {['慕尼黑机场问路', '餐厅点餐 (Bestellung)', '校园迎新 (Campus)'].map((theme) => (
                                <label key={theme} className="relative group cursor-pointer">
                                    <input type="radio" name="theme" className="peer sr-only" />
                                    <div className="border-2 border-gray-200 rounded-xl p-4 text-center hover:border-purple-200 peer-checked:border-purple-600 peer-checked:bg-purple-50 transition-all">
                                        <div className="font-medium text-gray-700 peer-checked:text-purple-700">{theme}</div>
                                    </div>
                                    <div className="absolute top-2 right-2 opacity-0 peer-checked:opacity-100 text-purple-600">
                                        <CheckCircle size={16} />
                                    </div>
                                </label>
                            ))}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* 2. 难度等级 */}
                        <div>
                            <label className="block text-sm font-bold text-gray-700 mb-2">难度等级 (Niveau)</label>
                            <select className="w-full border-gray-200 rounded-xl p-3 bg-gray-50 focus:bg-white focus:ring-2 focus:ring-purple-500 outline-none transition-all">
                                <option>A1 - 入门 (基础词汇)</option>
                                <option>A2 - 初级 (简单从句)</option>
                                <option>B1 - 进阶 (流利交流)</option>
                            </select>
                        </div>

                        {/* 3. AI 性格 */}
                        <div>
                            <label className="block text-sm font-bold text-gray-700 mb-2">AI 角色性格</label>
                            <select className="w-full border-gray-200 rounded-xl p-3 bg-gray-50 focus:bg-white focus:ring-2 focus:ring-purple-500 outline-none transition-all">
                                <option>友好耐心 (Encouraging)</option>
                                <option>严谨纠错 (Strict)</option>
                                <option>幽默风趣 (Humorous)</option>
                            </select>
                        </div>
                    </div>

                    {/* 4. 训练目标 */}
                    <div className="bg-purple-50 p-6 rounded-xl border border-purple-100">
                        <label className="block text-sm font-bold text-purple-900 mb-3">训练目标设定</label>
                        <div className="space-y-3">
                            <label className="flex items-center gap-3 bg-white p-3 rounded-lg border border-purple-100 cursor-pointer hover:shadow-sm transition-shadow">
                                <input type="checkbox" defaultChecked className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500" />
                                <span className="text-sm text-gray-700">强制使用完成时态 (Perfekt)</span>
                            </label>
                            <label className="flex items-center gap-3 bg-white p-3 rounded-lg border border-purple-100 cursor-pointer hover:shadow-sm transition-shadow">
                                <input type="checkbox" defaultChecked className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500" />
                                <span className="text-sm text-gray-700">包含至少 5 个 B1 级词汇</span>
                            </label>
                        </div>
                    </div>
                </div>

                {/* 底部按钮 */}
                <div className="p-6 border-t border-gray-100 bg-gray-50 flex justify-end gap-3">
                    <button onClick={() => navigate(-1)} className="px-6 py-2.5 text-gray-500 hover:bg-gray-200 rounded-xl font-medium transition-colors">取消</button>
                    <button
                        onClick={handlePublish}
                        disabled={isProcessing}
                        className="px-8 py-2.5 bg-purple-600 text-white rounded-xl font-bold hover:bg-purple-700 hover:shadow-lg hover:-translate-y-0.5 transition-all flex items-center gap-2"
                    >
                        {isProcessing ? '发布中...' : '确认发布任务'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ScenarioLaunch;