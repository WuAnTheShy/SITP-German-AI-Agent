import React, { useState, useRef, useEffect } from "react";
import StudentLayout from "../../components/StudentLayout";
import request from "../../api/request";
import { API_STUDENT_CHAT } from "../../api/config";
import {
  Send,
  Bot,
  User,
  Image as ImageIcon,
  Mic,
  Loader2,
} from "lucide-react";

const INITIAL_MSG = [
  {
    id: 1,
    sender: "ai",
    text: "Hallo! Ich bin dein KI-Tutor. Wie kann ich dir heute helfen? (你好！我是你的AI导师。今天我能为你做什么？)",
  },
];

const StudentHome = () => {
  const [messages, setMessages] = useState(() => {
    try {
      const saved = sessionStorage.getItem("studentHome_messages");
      return saved ? JSON.parse(saved) : INITIAL_MSG;
    } catch {
      return INITIAL_MSG;
    }
  });
  const [input, setInput] = useState("");

  // 消息变化时保存到 sessionStorage，切换页面后可恢复
  useEffect(() => {
    sessionStorage.setItem("studentHome_messages", JSON.stringify(messages));
  }, [messages]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const promptTemplates = [
    {
      name: "德语发音",
      text: "请帮我分析这个德语句子的发音规则，并标注每个单词的音标：[请输入德语句子]",
    },
    {
      name: "德语语法",
      text: "请解析这个德语句子的语法结构，包括时态、格位和从句类型：[请输入德语句子]",
    },
    {
      name: "德语词汇",
      text: "请帮我扩展这个德语单词的同义词、反义词和常用搭配：[请输入德语单词]",
    },
  ];

  const handleTemplateClick = (templateText) => {
    setInput(templateText);
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // AI 回复完成后自动聚焦输入框
  useEffect(() => {
    if (!loading) inputRef.current?.focus();
  }, [loading]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userText = input;
    const newMsg = { id: Date.now(), sender: "user", text: userText };
    setMessages((prev) => [...prev, newMsg]);
    setInput("");
    setLoading(true);
    try {
      const response = await request.post(API_STUDENT_CHAT, { message: userText }, { timeout: 60000 });
      const data = response.data;
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, sender: "ai", text: data.reply },
      ]);
    } catch (error) {
      console.error("请求失败:", error);
      const isTimeout = error.code === 'ECONNABORTED';
      setMessages(prev => [...prev, {
        id: Date.now() + 1, sender: 'ai',
        text: isTimeout
          ? '⚠️ AI 响应超时，请稍后重试。'
          : '⚠️ 连接失败。请确认后端服务是否正常运行。'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <StudentLayout>
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
        {/* 聊天消息区 */}
        <div className="flex-1 overflow-y-auto p-3 md:p-6 space-y-4 md:space-y-6 custom-scrollbar">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`flex items-start gap-2 md:gap-3 max-w-[90%] md:max-w-2xl ${msg.sender === "user" ? "flex-row-reverse" : ""}`}
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.sender === "user" ? "bg-blue-600" : "bg-green-600"}`}
                >
                  {msg.sender === "user" ? (
                    <User size={16} className="text-white" />
                  ) : (
                    <Bot size={16} className="text-white" />
                  )}
                </div>
                <div
                  className={`p-3 md:p-4 rounded-2xl whitespace-pre-wrap text-sm md:text-base ${msg.sender === "user"
                    ? "bg-blue-600 text-white rounded-tr-none shadow-md shadow-blue-500/10"
                    : "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm dark:shadow-gray-900/50 rounded-tl-none text-gray-800 dark:text-white"
                    }`}
                >
                  {msg.text}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center">
                  <Bot size={16} className="text-white" />
                </div>
                <div className="p-3 md:p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm dark:shadow-gray-900/50 rounded-2xl rounded-tl-none text-gray-500 dark:text-white flex items-center gap-2 text-sm md:text-base">
                  <Loader2 className="animate-spin" size={16} /> AI 正在思考...
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 提示词模板 */}
        <div className="p-4 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            📋 选择提示词模板
          </h3>
          <div className="flex flex-wrap gap-2">
            {promptTemplates.map((template, index) => (
              <button
                key={index}
                onClick={() => handleTemplateClick(template.text)}
                className="px-3 py-1 bg-blue-100 hover:bg-blue-200 dark:bg-blue-900/30 dark:hover:bg-blue-900/50 text-blue-800 dark:text-blue-400 rounded text-xs transition-colors border border-blue-200 dark:border-blue-800/50"
                disabled={loading}
              >
                {template.name}
              </button>
            ))}
          </div>
        </div>

        {/* 输入区 */}
        <div className="p-3 md:p-4 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 pb-safe">
          <div className="max-w-4xl mx-auto relative">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleSend()}
              placeholder={
                loading ? "请等待 AI 回复..." : "请输入德语与 AI 对话..."
              }
              disabled={loading}
              className="dark:text-white w-full pl-4 pr-32 py-4 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white dark:bg-gray-800 transition-all disabled:bg-gray-100 dark:bg-gray-800"
            />
            <div className="absolute right-2 top-2 bottom-2 flex items-center gap-1">
              <button className="p-2 text-gray-400 dark:text-gray-500 hover:text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:bg-blue-900/30 rounded-lg transition-colors">
                <ImageIcon size={20} />
              </button>
              <button className="p-2 text-gray-400 dark:text-gray-500 hover:text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:bg-blue-900/30 rounded-lg transition-colors">
                <Mic size={20} />
              </button>
              <button
                onClick={handleSend}
                disabled={loading}
                className={`p-2 rounded-lg transition-colors shadow-sm dark:shadow-gray-900/50 ${loading ? "bg-gray-400 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700 text-white"}`}
              >
                {loading ? (
                  <Loader2 size={18} className="animate-spin text-white" />
                ) : (
                  <Send size={18} />
                )}
              </button>
            </div>
          </div>
          <p className="text-center text-xs text-gray-400 dark:text-gray-500 mt-2">
            AI 可能会生成错误信息，请核对重要知识点。
          </p>
        </div>
      </div>
    </StudentLayout>
  );
};

export default StudentHome;
