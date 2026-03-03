import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import request from '../../api/request';
import { API_CHAT } from '../../api/config';
import { Send, Bot, User, ArrowLeft, Loader2, BookOpen, Brain, Activity } from 'lucide-react';

const TeacherAI = () => {
    const navigate = useNavigate();
    const [messages, setMessages] = useState([
        { id: 1, sender: 'ai', text: '您好，老师！我是您的 AI 教研助手。我可以帮您分析学情数据、制定教学计划或自动生成德语试卷，请问今天需要什么协助？' }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const promptTemplates = [
        { name: "分析学情", text: "请帮我分析一份班级平均分为78分的学情，指出学生普遍可能存在的薄弱环节，并给出教学建议。", icon: <Activity size={14} className="mr-1" /> },
        { name: "教案建议", text: "我们需要开始下一阶段的'德国文化与生活'主题教学，请帮我列出一个教学提纲和相关核心词汇。", icon: <BookOpen size={14} className="mr-1" /> },
        { name: "语法强化", text: "班里大部分学生在'虚拟式二式'掌握不好，请帮我出一道关于它的德语语法题目，附带解析。", icon: <Brain size={14} className="mr-1" /> }
    ];

    const handleTemplateClick = (templateText) => { setInput(templateText); };

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    const handleSend = async () => {
        if (!input.trim() || loading) return;
        const userText = input;
        const newMsg = { id: Date.now(), sender: 'user', text: userText };
        setMessages(prev => [...prev, newMsg]);
        setInput('');
        setLoading(true);
        try {
            const response = await request.post(API_CHAT, { message: userText });
            const data = response.data;
            setMessages(prev => [...prev, { id: Date.now() + 1, sender: 'ai', text: data.reply }]);
        } catch (error) {
            console.error("请求失败:", error);
            setMessages(prev => [...prev, {
                id: Date.now() + 1, sender: 'ai',
                text: '⚠️ 连接失败。请确认后端服务是否正常运行，或检查您的登录状态。'
            }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col items-center py-8">
            <div className="w-full max-w-5xl px-4 flex flex-col gap-6 h-[calc(100vh-4rem)]">
                {/* 顶部 Header 区 */}
                <div className="flex items-center gap-4 border-b border-gray-200 pb-4">
                    <button
                        onClick={() => navigate('/teacher/dashboard')}
                        className="bg-white p-2.5 rounded-full shadow hover:bg-gray-100 transition"
                        title="返回控制台"
                    >
                        <ArrowLeft size={20} className="text-gray-600" />
                    </button>
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                            <Bot size={28} className="text-indigo-600" />
                            AI 教研助手
                        </h1>
                        <p className="text-sm text-gray-500 mt-1">智能分析学情，自动化教务辅助</p>
                    </div>
                </div>

                {/* 主题聊天框 */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-200 flex-1 flex flex-col overflow-hidden">
                    {/* 聊天内容区 */}
                    <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-50/50">
                        {messages.map((msg) => (
                            <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                                <div className={`flex items-start gap-4 max-w-3xl ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}>
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-sm ${msg.sender === 'user' ? 'bg-indigo-600' : 'bg-white border border-gray-100'}`}>
                                        {msg.sender === 'user' ? <User size={20} className="text-white" /> : <Bot size={24} className="text-indigo-600" />}
                                    </div>
                                    <div className={`p-4 rounded-2xl text-base leading-relaxed whitespace-pre-wrap shadow-sm ${msg.sender === 'user'
                                        ? 'bg-indigo-600 text-white rounded-tr-none'
                                        : 'bg-white border border-gray-100 rounded-tl-none text-gray-800'
                                        }`}>
                                        {msg.text}
                                    </div>
                                </div>
                            </div>
                        ))}
                        {loading && (
                            <div className="flex justify-start">
                                <div className="flex items-start gap-4">
                                    <div className="w-10 h-10 rounded-full bg-white border border-gray-100 flex items-center justify-center shadow-sm">
                                        <Bot size={24} className="text-indigo-600" />
                                    </div>
                                    <div className="p-4 bg-white border border-gray-100 shadow-sm rounded-2xl rounded-tl-none text-gray-500 flex items-center gap-2">
                                        <Loader2 className="animate-spin text-indigo-500" size={18} /> AI 助教正在分析您的需求...
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* 提示词模板 */}
                    <div className="p-4 bg-white border-t border-gray-100">
                        <div className="flex flex-wrap gap-3">
                            {promptTemplates.map((template, index) => (
                                <button key={index} onClick={() => handleTemplateClick(template.text)}
                                    className="px-4 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-xl text-sm font-medium transition-colors flex items-center border border-indigo-100"
                                    disabled={loading}>
                                    {template.icon}
                                    {template.name}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* 下部输入区 */}
                    <div className="p-5 bg-white border-t border-gray-100">
                        <div className="flex max-w-5xl mx-auto items-center gap-3">
                            <input type="text" value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                                placeholder={loading ? "正在处理请求..." : "输入您要咨询的教研问题或指令..."}
                                disabled={loading}
                                className="flex-1 px-5 py-4 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all disabled:bg-gray-100 text-gray-700"
                            />
                            <button onClick={handleSend} disabled={loading}
                                className={`px-6 py-4 rounded-xl font-bold transition-colors shadow-sm flex items-center gap-2 ${loading ? 'bg-gray-300 text-gray-500 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 text-white'}`}>
                                {loading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
                                发送
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TeacherAI;
