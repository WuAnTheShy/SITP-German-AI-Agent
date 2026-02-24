import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, BookOpen, Mic, Image as ImageIcon, Loader2 } from 'lucide-react';

const StudentHome = () => {
    // 1. 状态管理
    const [messages, setMessages] = useState([
        { id: 1, sender: 'ai', text: 'Hallo! Ich bin dein KI-Tutor. Wie kann ich dir heute helfen? (你好！我是你的AI导师。今天我能为你做什么？)' }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false); // 新增：加载状态
    const messagesEndRef = useRef(null); // 新增：用于自动滚动

    // 2. 提示词模板
    const promptTemplates = [
        {
            name: "德语发音",
            text: "请帮我分析这个德语句子的发音规则，并标注每个单词的音标：[请输入德语句子]"
        },
        {
            name: "德语语法",
            text: "请解析这个德语句子的语法结构，包括时态、格位和从句类型：[请输入德语句子]"
        },
        {
            name: "德语词汇",
            text: "请帮我扩展这个德语单词的同义词、反义词和常用搭配：[请输入德语单词]"
        }
    ];

    const handleTemplateClick = (templateText) => {
        setInput(templateText);
    };

    // 3. 自动滚动到底部
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    // 4. 发送消息 (核心修改部分)
    const handleSend = async () => {
        if (!input.trim() || loading) {
            return;
        }

        // (1) 立即显示用户消息
        const userText = input;
        const newMsg = { id: Date.now(), sender: 'user', text: userText };
        setMessages(prev => [...prev, newMsg]);
        setInput('');
        setLoading(true);

        try {
            // (2) 发送给 Python 后端
            const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:9000/api/chat';

            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: userText })
            });

            // (3) 解析后端返回的数据
            const data = await response.json();

            if (response.ok) {
                const aiMsg = {
                    id: Date.now() + 1,
                    sender: 'ai',
                    text: data.reply // 这里用后端返回的真实 reply
                };
                setMessages(prev => [...prev, aiMsg]);
            } else {
                throw new Error('后端报错了');
            }

        } catch (error) {
            console.error("请求失败:", error);
            const errorMsg = {
                id: Date.now() + 1,
                sender: 'ai',
                text: '⚠️ 连接失败。请确认：\n1. Python 黑色窗口是否开着？\n2. 只有 localhost:5173 能访问，GitHub 远程网页无法访问本地后端。'
            };
            setMessages(prev => [...prev, errorMsg]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex h-screen bg-gray-50">
            {/* 左侧导航栏 */}
            <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
                <div className="p-6 border-b border-gray-100">
                    <h2 className="text-xl font-bold text-blue-900 flex items-center gap-2">
                        <Bot size={24} /> AI-Tutor
                    </h2>
                </div>
                <nav className="flex-1 p-4 space-y-2">
                    <button className="w-full text-left px-4 py-3 bg-blue-50 text-blue-700 rounded-lg font-medium flex items-center gap-3">
                        <Bot size={18} /> 智能对话
                    </button>
                    <button className="w-full text-left px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-lg font-medium flex items-center gap-3 transition-colors">
                        <BookOpen size={18} /> 学习路径
                    </button>
                </nav>
                <div className="p-4 border-t border-gray-100">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold">
                            WS
                        </div>
                        <div>
                            <p className="text-sm font-bold text-gray-700">魏同学</p>
                            <p className="text-xs text-gray-400">在线</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* 右侧聊天主区域 */}
            <div className="flex-1 flex flex-col">
                {/* 聊天记录 */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {messages.map((msg) => (
                        <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`flex items-start gap-3 max-w-2xl ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}>
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.sender === 'user' ? 'bg-blue-600' : 'bg-green-600'}`}>
                                    {msg.sender === 'user' ? <User size={16} className="text-white" /> : <Bot size={16} className="text-white" />}
                                </div>
                                <div className={`p-4 rounded-2xl whitespace-pre-wrap ${msg.sender === 'user'
                                    ? 'bg-blue-600 text-white rounded-tr-none'
                                    : 'bg-white border border-gray-200 shadow-sm rounded-tl-none text-gray-800'
                                    }`}>
                                    {msg.text}
                                </div>
                            </div>
                        </div>
                    ))}

                    {/* 加载中动画 */}
                    {loading && (
                        <div className="flex justify-start">
                            <div className="flex items-start gap-3">
                                <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center">
                                    <Bot size={16} className="text-white" />
                                </div>
                                <div className="p-4 bg-white border border-gray-200 shadow-sm rounded-2xl rounded-tl-none text-gray-500 flex items-center gap-2">
                                    <Loader2 className="animate-spin" size={16} />
                                    AI 正在思考...
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* 提示词模板选择区 */}
                <div className="p-4 bg-gray-50 border-b border-gray-200">
                    <h3 className="text-sm font-medium text-gray-700 mb-2">📋 选择提示词模板</h3>
                    <div className="flex flex-wrap gap-2">
                        {promptTemplates.map((template, index) => (
                            <button
                                key={index}
                                onClick={() => handleTemplateClick(template.text)}
                                className="px-3 py-1 bg-blue-100 hover:bg-blue-200 text-blue-800 rounded text-xs transition-colors"
                                disabled={loading}
                            >
                                {template.name}
                            </button>
                        ))}
                    </div>
                </div>

                {/* 输入框区域 */}
                <div className="p-4 bg-white border-t border-gray-200">
                    <div className="max-w-4xl mx-auto relative">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                            placeholder={loading ? "请等待 AI 回复..." : "请输入德语与 AI 对话..."}
                            disabled={loading}
                            className="w-full pl-4 pr-32 py-4 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all disabled:bg-gray-100"
                        />
                        <div className="absolute right-2 top-2 bottom-2 flex items-center gap-1">
                            <button className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                                <ImageIcon size={20} />
                            </button>
                            <button className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                                <Mic size={20} />
                            </button>
                            <button
                                onClick={handleSend}
                                disabled={loading}
                                className={`p-2 rounded-lg transition-colors shadow-sm ${loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 text-white'
                                    }`}
                            >
                                {loading ? <Loader2 size={18} className="animate-spin text-white" /> : <Send size={18} />}
                            </button>
                        </div>
                    </div>
                    <p className="text-center text-xs text-gray-400 mt-2">
                        AI 可能会生成错误信息，请核对重要知识点。
                    </p>
                </div>
            </div>
        </div>
    );
};

export default StudentHome;