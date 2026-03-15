import React, { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import request from "../../api/request";
import {
  API_CHAT,
  API_TEACHER_CHAT_NEW,
  API_TEACHER_CHAT_SESSIONS,
  API_TEACHER_CHAT_MESSAGES,
  API_TEACHER_CHAT_SESSION,
} from "../../api/config";
import {
  Send,
  Bot,
  User,
  ArrowLeft,
  Loader2,
  BookOpen,
  Brain,
  Activity,
  Plus,
  MessageSquare,
  Trash2,
  PanelLeftClose,
  PanelLeft,
} from "lucide-react";

const WELCOME_AI =
  "您好，老师！我是您的 AI 教研助手。我可以帮您分析学情数据、制定教学计划或自动生成德语试卷，请问今天需要什么协助？";

const welcomeMessages = () => [
  { id: "w1", sender: "ai", text: WELCOME_AI },
];

const TeacherAI = () => {
  const navigate = useNavigate();
  const userInfo = JSON.parse(localStorage.getItem("userInfo") || "{}");
  const [messages, setMessages] = useState(welcomeMessages());
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarDesktopOpen, setSidebarDesktopOpen] = useState(true);
  const [deleteTargetId, setDeleteTargetId] = useState(null);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const loadSessions = useCallback(() => {
    request
      .get(API_TEACHER_CHAT_SESSIONS)
      .then((r) => {
        const list = r.data?.data ?? r.data ?? [];
        setSessions(Array.isArray(list) ? list : []);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const r = await request.get(API_TEACHER_CHAT_SESSIONS).catch(() => null);
      if (cancelled || !r) return;
      const list = r.data?.data ?? r.data ?? [];
      const arr = Array.isArray(list) ? list : [];
      setSessions(arr);
      if (arr.length === 0) {
        const nr = await request.post(API_TEACHER_CHAT_NEW).catch(() => null);
        if (cancelled || !nr) return;
        const id = nr.data?.data?.session_id ?? nr.data?.session_id;
        if (id) {
          setSessionId(id);
          setMessages(welcomeMessages());
          setSessions([
            {
              id,
              title: null,
              closed: false,
              updated_at: new Date().toISOString(),
            },
          ]);
        }
        return;
      }
      const open = arr.find((s) => !s.closed) || arr[0];
      if (open && !cancelled) {
        setSessionId(open.id);
        const mr = await request
          .get(API_TEACHER_CHAT_MESSAGES, { params: { session_id: open.id } })
          .catch(() => null);
        if (cancelled || !mr) return;
        const msgs = mr.data?.data ?? mr.data ?? [];
        if (Array.isArray(msgs) && msgs.length > 0) {
          setMessages(
            msgs.map((m) => ({
              id: m.id,
              sender: m.role === "user" ? "user" : "ai",
              text: m.content,
            }))
          );
        } else setMessages(welcomeMessages());
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const loadSessionMessages = async (sid) => {
    if (!sid) {
      setMessages(welcomeMessages());
      return;
    }
    setLoadingMessages(true);
    try {
      const r = await request.get(API_TEACHER_CHAT_MESSAGES, {
        params: { session_id: sid },
      });
      const list = r.data?.data ?? r.data ?? [];
      if (!Array.isArray(list) || list.length === 0) {
        setMessages(welcomeMessages());
        return;
      }
      setMessages(
        list.map((m) => ({
          id: m.id,
          sender: m.role === "user" ? "user" : "ai",
          text: m.content,
        }))
      );
    } catch {
      setMessages(welcomeMessages());
    } finally {
      setLoadingMessages(false);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, loadingMessages]);

  useEffect(() => {
    if (!loading && !loadingMessages) inputRef.current?.focus();
  }, [loading, loadingMessages]);

  const handleSelectSession = async (s) => {
    setSessionId(s.id);
    await loadSessionMessages(s.id);
    if (window.innerWidth < 768) setSidebarOpen(false);
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userText = input;
    setMessages((prev) => [
      ...prev,
      { id: `u-${Date.now()}`, sender: "user", text: userText },
    ]);
    setInput("");
    setLoading(true);
    try {
      const response = await request.post(
        API_CHAT,
        {
          message: userText,
          session_id: sessionId || undefined,
          new_thread: false,
        },
        { timeout: 90000 }
      );
      const data = response.data;
      if (data.session_id) setSessionId(data.session_id);
      setMessages((prev) => [
        ...prev,
        { id: `a-${Date.now()}`, sender: "ai", text: data.reply || "（无回复）" },
      ]);
      loadSessions();
    } catch (error) {
      console.error(error);
      const isTimeout = error.code === "ECONNABORTED";
      setMessages((prev) => [
        ...prev,
        {
          id: `e-${Date.now()}`,
          sender: "ai",
          text: isTimeout
            ? "⚠️ AI 响应超时，请稍后重试。"
            : "⚠️ 连接失败，请确认后端已启动并已登录。",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = async () => {
    try {
      const r = await request.post(API_TEACHER_CHAT_NEW);
      const id = r.data?.data?.session_id ?? r.data?.session_id;
      if (id) {
        setSessionId(id);
        setMessages(welcomeMessages());
        loadSessions();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const confirmDeleteSession = async () => {
    if (!deleteTargetId) return;
    const deletedId = deleteTargetId;
    setDeleteTargetId(null);
    try {
      await request.delete(`${API_TEACHER_CHAT_SESSION}/${deletedId}`);
      const r = await request.get(API_TEACHER_CHAT_SESSIONS);
      const arr = Array.isArray(r.data?.data)
        ? r.data.data
        : Array.isArray(r.data)
          ? r.data
          : [];
      setSessions(arr);
      if (sessionId === deletedId) {
        if (arr.length === 0) {
          const nr = await request.post(API_TEACHER_CHAT_NEW);
          const nid = nr.data?.data?.session_id ?? nr.data?.session_id;
          if (nid) {
            setSessionId(nid);
            setMessages(welcomeMessages());
            loadSessions();
          } else {
            setSessionId(null);
            setMessages(welcomeMessages());
          }
        } else {
          const next = arr[0];
          setSessionId(next.id);
          await loadSessionMessages(next.id);
        }
      }
    } catch (e) {
      console.error(e);
      loadSessions();
    }
  };

  const promptTemplates = [
    {
      name: "分析学情",
      text: "请帮我分析一份班级平均分为78分的学情，指出学生普遍可能存在的薄弱环节，并给出教学建议。",
      icon: <Activity size={14} className="mr-1" />,
    },
    {
      name: "教案建议",
      text: "我们需要开始下一阶段的'德国文化与生活'主题教学，请帮我列出一个教学提纲和相关核心词汇。",
      icon: <BookOpen size={14} className="mr-1" />,
    },
    {
      name: "语法强化",
      text: "班里大部分学生在'虚拟式二式'掌握不好，请帮我出一道关于它的德语语法题目，附带解析。",
      icon: <Brain size={14} className="mr-1" />,
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
      {/* 顶部：返回 + 标题 */}
      <div className="shrink-0 flex items-center gap-4 px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <button
          onClick={() => navigate(`/teacher/${userInfo.id}/dashboard`)}
          className="p-2.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition"
          title="返回控制台"
        >
          <ArrowLeft size={20} className="text-gray-600 dark:text-gray-400" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-gray-800 dark:text-gray-200 flex items-center gap-2">
            <Bot size={24} className="text-indigo-600 dark:text-indigo-400" />
            AI 教研助手
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            智能分析学情，自动化教务辅助
          </p>
        </div>
      </div>

      <div className="flex-1 flex min-h-0 overflow-hidden">
        {/* 侧栏 */}
        <aside
          className={`${
            sidebarOpen ? "flex" : "hidden"
          } ${sidebarDesktopOpen ? "md:flex" : "md:hidden"} w-full md:w-72 shrink-0 flex-col border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900`}
        >
          <div className="p-3 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <MessageSquare
                className="text-indigo-600 shrink-0"
                size={20}
              />
              <span className="font-semibold text-gray-800 dark:text-gray-100 truncate text-sm">
                对话历史
              </span>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              <button
                type="button"
                onClick={handleNewChat}
                className="p-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
                title="新对话"
              >
                <Plus size={18} />
              </button>
              <button
                type="button"
                className="hidden md:flex p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
                title="收起历史列表"
                onClick={() => setSidebarDesktopOpen(false)}
              >
                <PanelLeftClose size={18} />
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {sessions.map((s) => (
              <div
                key={s.id}
                className={`flex items-stretch gap-0 rounded-lg overflow-hidden ${
                  sessionId === s.id
                    ? "bg-indigo-100 dark:bg-indigo-900/40"
                    : "hover:bg-gray-100 dark:hover:bg-gray-800"
                }`}
              >
                <button
                  type="button"
                  onClick={() => handleSelectSession(s)}
                  className={`flex-1 text-left px-3 py-2.5 text-sm min-w-0 ${
                    sessionId === s.id
                      ? "text-indigo-900 dark:text-indigo-100"
                      : "text-gray-700 dark:text-gray-300"
                  }`}
                >
                  <div className="truncate font-medium" title={`#${s.id}`}>
                    {s.title || `对话 #${s.id}`}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {s.closed ? "已暂停 · " : "进行中 · "}
                    {s.updated_at ? s.updated_at.slice(0, 10) : ""}
                    {s.title ? ` · #${s.id}` : ""}
                  </div>
                </button>
                <button
                  type="button"
                  title="删除此对话"
                  className="shrink-0 px-2 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/50"
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeleteTargetId(s.id);
                  }}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
            {sessions.length === 0 && (
              <p className="text-xs text-gray-500 p-2">暂无记录，点右上角 + 开始</p>
            )}
          </div>
          <button
            type="button"
            className="md:hidden p-3 text-sm text-indigo-600 border-t border-gray-200 dark:border-gray-800"
            onClick={() => setSidebarOpen(false)}
          >
            收起列表
          </button>
        </aside>

        {/* 主区 */}
        <div className="flex-1 flex flex-col min-w-0 min-h-0">
          <div className="md:hidden flex items-center gap-2 p-2 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
            <button
              type="button"
              className="p-2 rounded-lg bg-gray-100 dark:bg-gray-800"
              onClick={() => setSidebarOpen(true)}
            >
              <MessageSquare size={18} />
            </button>
            <span className="font-medium text-gray-800 dark:text-gray-100">
              对话历史
            </span>
            <button
              type="button"
              onClick={handleNewChat}
              className="ml-auto p-2 rounded-lg bg-indigo-600 text-white"
            >
              <Plus size={18} />
            </button>
          </div>

          <div className="hidden md:flex items-center gap-2 px-4 py-2 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
            {!sidebarDesktopOpen && (
              <button
                type="button"
                className="p-2 rounded-lg text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 dark:text-gray-300"
                title="展开对话历史"
                onClick={() => setSidebarDesktopOpen(true)}
              >
                <PanelLeft size={20} />
              </button>
            )}
            <span className="text-sm text-gray-600 dark:text-gray-400 truncate">
              {sessionId
                ? `当前 · #${sessionId}${sidebarDesktopOpen ? "（左侧可切换）" : ""}`
                : "请选择或新建对话"}
            </span>
          </div>

          <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 bg-gray-50 dark:bg-gray-900/50">
            {loadingMessages ? (
              <div className="flex justify-center py-8 text-gray-500">
                <Loader2 className="animate-spin mr-2" /> 加载历史…
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${
                    msg.sender === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`flex items-start gap-3 max-w-[90%] md:max-w-2xl ${
                      msg.sender === "user" ? "flex-row-reverse" : ""
                    }`}
                  >
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${
                        msg.sender === "user"
                          ? "bg-indigo-600"
                          : "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700"
                      }`}
                    >
                      {msg.sender === "user" ? (
                        <User size={20} className="text-white" />
                      ) : (
                        <Bot size={24} className="text-indigo-600 dark:text-indigo-400" />
                      )}
                    </div>
                    <div
                      className={`p-4 rounded-2xl text-base whitespace-pre-wrap ${
                        msg.sender === "user"
                          ? "bg-indigo-600 text-white rounded-tr-none"
                          : "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-tl-none text-gray-800 dark:text-gray-200"
                      }`}
                    >
                      {msg.text}
                    </div>
                  </div>
                </div>
              ))
            )}
            {loading && (
              <div className="flex justify-start">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 flex items-center justify-center">
                    <Bot size={24} className="text-indigo-600 dark:text-indigo-400" />
                  </div>
                  <div className="p-4 rounded-2xl rounded-tl-none bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 flex items-center gap-2 text-gray-500">
                    <Loader2 className="animate-spin text-indigo-500" size={18} />{" "}
                    AI 助教正在分析您的需求...
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-4 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
            <div className="flex flex-wrap gap-3 mb-3">
              {promptTemplates.map((template, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => setInput(template.text)}
                  className="px-4 py-2 bg-indigo-50 dark:bg-indigo-900/30 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 text-indigo-700 dark:text-indigo-400 rounded-xl text-sm font-medium border border-indigo-100 dark:border-indigo-800/50 flex items-center"
                  disabled={loading}
                >
                  {template.icon}
                  {template.name}
                </button>
              ))}
            </div>
            <div className="flex gap-3 max-w-4xl mx-auto">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder={
                  loading ? "正在处理请求..." : "输入您要咨询的教研问题或指令..."
                }
                disabled={loading}
                className="flex-1 px-5 py-4 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-700 dark:text-white disabled:opacity-60"
              />
              <button
                onClick={handleSend}
                disabled={loading || !sessionId}
                className={`px-6 py-4 rounded-xl font-bold flex items-center gap-2 ${
                  loading || !sessionId
                    ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                    : "bg-indigo-600 hover:bg-indigo-700 text-white"
                }`}
              >
                {loading ? (
                  <Loader2 size={20} className="animate-spin" />
                ) : (
                  <Send size={20} />
                )}
                发送
              </button>
            </div>
            {!sessionId && (
              <p className="text-center text-xs text-amber-600 mt-2">
                请先在左侧选一个会话，或点 + 新建对话
              </p>
            )}
          </div>
        </div>
      </div>

      {/* 删除确认弹窗 */}
      {deleteTargetId != null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-xl max-w-md w-full p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              删除这条对话？
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
              将永久删除对话 <strong>#{deleteTargetId}</strong> 及其全部聊天记录，<strong>无法恢复</strong>。确定要继续吗？
            </p>
            <div className="flex gap-3 justify-end">
              <button
                type="button"
                className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200"
                onClick={() => setDeleteTargetId(null)}
              >
                取消
              </button>
              <button
                type="button"
                className="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700"
                onClick={confirmDeleteSession}
              >
                确定删除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeacherAI;
