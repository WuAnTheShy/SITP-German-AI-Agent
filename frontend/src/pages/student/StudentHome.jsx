import React, { useState, useRef, useEffect, useCallback } from "react";
import StudentLayout from "../../components/StudentLayout";
import request from "../../api/request";
import { parseStoredUserInfo } from "../../utils/safeJson";
import {
  API_STUDENT_CHAT,
  API_STUDENT_CHAT_NEW,
  API_STUDENT_CHAT_SESSIONS,
  API_STUDENT_CHAT_MESSAGES,
  API_STUDENT_CHAT_SESSION,
  API_USER_KB_DOCS,
  API_USER_KB_UPLOAD_TEMP,
  API_STUDENT_CHAT_STREAM,
} from "../../api/config";
import { streamChat } from "../../api/streamingChat";
import AgentProgress from "../../components/AgentProgress";
import {
  Send,
  Bot,
  User,
  Loader2,
  Plus,
  MessageSquare,
  Trash2,
  PanelLeftClose,
  PanelLeft,
  Upload,
} from "lucide-react";
import MarkdownContent from "../../components/MarkdownContent";

const WELCOME_AI =
  "Hallo! Ich bin dein KI-Tutor. Wie kann ich dir heute helfen? (你好！我是你的AI导师。今天我能为你做什么？)";

const welcomeMessages = () => [{ id: "w1", sender: "ai", text: WELCOME_AI }];

const StudentHome = () => {
  const [messages, setMessages] = useState(() => welcomeMessages());
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarDesktopOpen, setSidebarDesktopOpen] = useState(true);
  const [deleteTargetId, setDeleteTargetId] = useState(null);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [kbUploading, setKbUploading] = useState(false);
  const [kbHint, setKbHint] = useState("");
  const [kbDocs, setKbDocs] = useState([]);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const userInfo = parseStoredUserInfo();
  const myKbHref = userInfo.id
    ? `#/student/${userInfo.id}/my-kb`
    : "#/student/login";

  const loadSessions = useCallback(() => {
    request
      .get(API_STUDENT_CHAT_SESSIONS)
      .then((r) => {
        const list = r.data?.data ?? r.data ?? [];
        setSessions(Array.isArray(list) ? list : []);
      })
      .catch(() => {});
  }, []);

  const loadKbDocs = useCallback(async () => {
    try {
      const r = await request.get(API_USER_KB_DOCS, { timeout: 60000 });
      const list = Array.isArray(r.data) ? r.data : [];
      setKbDocs(list);
    } catch {
      setKbDocs([]);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const r = await request.get(API_STUDENT_CHAT_SESSIONS).catch(() => null);
      if (cancelled || !r) return;
      const list = r.data?.data ?? r.data ?? [];
      const arr = Array.isArray(list) ? list : [];
      setSessions(arr);
      if (arr.length === 0) {
        const nr = await request.post(API_STUDENT_CHAT_NEW).catch(() => null);
        if (cancelled || !nr) return;
        const id = nr.data?.data?.session_id ?? nr.data?.session_id;
        if (id) {
          setSessionId(id);
          setMessages(welcomeMessages());
          setSessions([
            {
              id,
              title: "进行中",
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
          .get(API_STUDENT_CHAT_MESSAGES, { params: { session_id: open.id } })
          .catch(() => null);
        if (cancelled || !mr) return;
        const msgs = mr.data?.data ?? mr.data ?? [];
        if (Array.isArray(msgs) && msgs.length > 0) {
          setMessages(
            msgs.map((m) => ({
              id: m.id,
              sender: m.role === "user" ? "user" : "ai",
              text: m.content,
            })),
          );
        } else setMessages(welcomeMessages());
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    loadKbDocs();
  }, [loadKbDocs]);

  const loadSessionMessages = async (sid) => {
    if (!sid) {
      setMessages(welcomeMessages());
      return;
    }
    setLoadingMessages(true);
    try {
      const r = await request.get(API_STUDENT_CHAT_MESSAGES, {
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
        })),
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

  // const handleSend = async () => {
  //   if (!input.trim() || loading) return;
  //   const userText = input;
  //   setMessages((prev) => [
  //     ...prev,
  //     { id: `u-${Date.now()}`, sender: "user", text: userText },
  //   ]);
  //   setInput("");
  //   setLoading(true);
  //   try {
  //     const response = await request.post(
  //       API_STUDENT_CHAT,
  //       {
  //         message: userText,
  //         session_id: sessionId || undefined,
  //         new_thread: false,
  //       },
  //       { timeout: 90000 },
  //     );
  //     const data = response.data;
  //     if (data.session_id) setSessionId(data.session_id);
  //     setMessages((prev) => [
  //       ...prev,
  //       {
  //         id: `a-${Date.now()}`,
  //         sender: "ai",
  //         text: data.reply || "（无回复）",
  //       },
  //     ]);
  //     loadSessions();
  //   } catch (error) {
  //     console.error(error);
  //     const isTimeout = error.code === "ECONNABORTED";
  //     setMessages((prev) => [
  //       ...prev,
  //       {
  //         id: `e-${Date.now()}`,
  //         sender: "ai",
  //         text: isTimeout
  //           ? "⚠️ AI 响应超时，请稍后重试。"
  //           : "⚠️ 连接失败，请确认后端已启动并已登录。",
  //       },
  //     ]);
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userText = input;
    const userMsgId = `u-${Date.now()}`;
    const aiMsgId = `a-${Date.now()}`;

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, sender: "user", text: userText },
      // 占位 AI 消息,用于流式更新 text + stages
      { id: aiMsgId, sender: "ai", text: "", stages: [], streaming: true },
    ]);
    setInput("");
    setLoading(true);

    let aiText = "";

    const stop = streamChat(
      API_STUDENT_CHAT_STREAM,
      {
        message: userText,
        session_id: sessionId || undefined,
        new_thread: false,
      },
      {
        onMeta: (data) => {
          if (data.session_id) setSessionId(data.session_id);
        },
        onRagStart: () => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiMsgId
                ? {
                    ...m,
                    stages: [
                      ...(m.stages || []),
                      {
                        type: "rag",
                        label: "检索知识库...",
                        status: "running",
                      },
                    ],
                  }
                : m,
            ),
          );
        },
        onRagDone: (data) => {
          setMessages((prev) =>
            prev.map((m) => {
              if (m.id !== aiMsgId) return m;
              const stages = [...(m.stages || [])];
              const idx = stages.findIndex(
                (s) => s.type === "rag" && s.status === "running",
              );
              if (idx >= 0) {
                stages[idx] = {
                  ...stages[idx],
                  status: "done",
                  summary: data.used
                    ? `命中 ${data.sources_count} 条 (top=${data.top_score})`
                    : "未命中,使用通用知识",
                };
              }
              return { ...m, stages };
            }),
          );
        },
        onToolCallStart: (data) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiMsgId
                ? {
                    ...m,
                    stages: [
                      ...(m.stages || []),
                      {
                        type: "tool",
                        label: `调用工具: ${data.display_name || data.name}`,
                        status: "running",
                        toolName: data.name,
                      },
                    ],
                  }
                : m,
            ),
          );
        },
        onToolCallDone: (data) => {
          setMessages((prev) =>
            prev.map((m) => {
              if (m.id !== aiMsgId) return m;
              const stages = [...(m.stages || [])];
              const idx = stages.findIndex(
                (s) =>
                  s.type === "tool" &&
                  s.toolName === data.name &&
                  s.status === "running",
              );
              if (idx >= 0) {
                stages[idx] = {
                  ...stages[idx],
                  status: data.success ? "done" : "failed",
                  summary: data.summary,
                };
              }
              return { ...m, stages };
            }),
          );
        },
        onToken: (delta) => {
          aiText += delta;
          setMessages((prev) =>
            prev.map((m) => (m.id === aiMsgId ? { ...m, text: aiText } : m)),
          );
        },
        onDone: () => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiMsgId ? { ...m, streaming: false } : m,
            ),
          );
          setLoading(false);
          loadSessions();
        },
        onError: (err) => {
          console.error(err);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiMsgId
                ? {
                    ...m,
                    text: aiText || "⚠️ 连接失败,请确认后端已启动并已登录。",
                    streaming: false,
                  }
                : m,
            ),
          );
          setLoading(false);
        },
      },
    );

    // 可选:用户取消按钮可调 stop()——本次先不加 UI
    void stop;
  };

  const handleKbUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file || kbUploading) return;
    const fd = new FormData();
    fd.append("file", file);
    setKbHint("");
    setKbUploading(true);
    try {
      if (!sessionId) {
        throw new Error("请先创建或选择一个会话");
      }
      const uploadUrl = `${API_USER_KB_UPLOAD_TEMP}?session_key=${encodeURIComponent(`student:${sessionId}`)}`;
      await request.post(uploadUrl, fd, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 600000,
      });
      setKbHint(`已加入本会话：${file.name}`);
      window.setTimeout(() => setKbHint(""), 3500);
      await loadKbDocs();
    } catch (err) {
      setKbHint(
        `上传失败：${err.response?.data?.detail || err.message || "请稍后重试"}`,
      );
    } finally {
      setKbUploading(false);
      e.target.value = "";
    }
  };

  const handleNewChat = async () => {
    try {
      const r = await request.post(API_STUDENT_CHAT_NEW);
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
      await request.delete(`${API_STUDENT_CHAT_SESSION}/${deletedId}`);
      const r = await request.get(API_STUDENT_CHAT_SESSIONS);
      const arr = Array.isArray(r.data?.data)
        ? r.data.data
        : Array.isArray(r.data)
          ? r.data
          : [];
      setSessions(arr);
      if (sessionId === deletedId) {
        if (arr.length === 0) {
          const nr = await request.post(API_STUDENT_CHAT_NEW);
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
      name: "德语发音",
      text: "请帮我分析这个德语句子的发音规则…[请输入德语句子]",
    },
    { name: "德语语法", text: "请解析这个德语句子的语法结构…[请输入德语句子]" },
    {
      name: "德语词汇",
      text: "请帮我扩展这个德语单词的同义词、反义词…[请输入德语单词]",
    },
  ];
  const currentSessionKey = sessionId ? `student:${sessionId}` : null;
  const currentSessionTempDocs = kbDocs.filter(
    (d) =>
      d.is_temporary &&
      currentSessionKey &&
      d.session_key === currentSessionKey,
  );

  return (
    <StudentLayout>
      <div className="flex-1 flex min-h-0 overflow-hidden bg-transparent">
        {/* 侧栏：会话列表；桌面可收起 */}
        <aside
          className={`${
            sidebarOpen ? "flex" : "hidden"
          } ${sidebarDesktopOpen ? "md:flex" : "md:hidden"} w-full md:w-72 shrink-0 flex-col border-r border-slate-200/70 dark:border-slate-700/70 student-panel`}
        >
          <div className="p-3 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <MessageSquare className="text-blue-600 shrink-0" size={20} />
              <span className="font-semibold text-gray-800 dark:text-gray-100 truncate text-sm">
                智能对话
              </span>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              <button
                type="button"
                onClick={handleNewChat}
                className="p-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
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
          <div className="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
            {sessions.map((s) => (
              <div
                key={s.id}
                className={`flex items-stretch gap-0 rounded-lg overflow-hidden ${
                  sessionId === s.id
                    ? "bg-blue-100 dark:bg-blue-900/40"
                    : "hover:bg-gray-100 dark:hover:bg-gray-800"
                }`}
              >
                <button
                  type="button"
                  onClick={() => handleSelectSession(s)}
                  className={`flex-1 text-left px-3 py-2.5 text-sm min-w-0 ${
                    sessionId === s.id
                      ? "text-blue-900 dark:text-blue-100"
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
              <p className="text-xs text-gray-500 p-2">
                暂无记录，点右上角 + 开始
              </p>
            )}
          </div>
          <button
            type="button"
            className="md:hidden p-3 text-sm text-blue-600 border-t border-gray-200 dark:border-gray-800"
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
              智能对话
            </span>
            <button
              type="button"
              onClick={handleNewChat}
              className="ml-auto p-2 rounded-lg bg-blue-600 text-white"
            >
              <Plus size={18} />
            </button>
          </div>

          <div className="hidden md:flex items-center gap-2 px-4 py-2 border-b border-slate-200/70 dark:border-slate-700/70 student-panel">
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

          <div className="flex-1 overflow-y-auto p-3 md:p-6 space-y-4 custom-scrollbar bg-transparent">
            {loadingMessages ? (
              <div className="flex justify-center py-8 text-gray-500">
                <Loader2 className="animate-spin mr-2" /> 加载历史…
              </div>
            ) : (
              (Array.isArray(messages) ? messages : []).map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`flex items-start gap-2 max-w-[90%] md:max-w-2xl ${
                      msg.sender === "user" ? "flex-row-reverse" : ""
                    }`}
                  >
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                        msg.sender === "user" ? "bg-blue-600" : "bg-green-600"
                      }`}
                    >
                      {msg.sender === "user" ? (
                        <User size={16} className="text-white" />
                      ) : (
                        <Bot size={16} className="text-white" />
                      )}
                    </div>
                    <div
                      className={`p-3 md:p-4 rounded-2xl text-sm md:text-base ${
                        msg.sender === "user"
                          ? "bg-blue-600 text-white rounded-tr-none"
                          : "student-card rounded-tl-none text-gray-800 dark:text-white"
                      }`}
                    >
                      {msg.sender === "user" ? (
                        <span className="whitespace-pre-wrap">{msg.text}</span>
                      ) : (
                        <>
                          {msg.stages && msg.stages.length > 0 && (
                            <AgentProgress stages={msg.stages} />
                          )}
                          {msg.text ? (
                            <MarkdownContent content={msg.text} />
                          ) : msg.streaming ? (
                            <span className="text-slate-400 text-xs italic">
                              AI 正在准备回答...
                            </span>
                          ) : null}
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
            {/* {loading && (
              <div className="flex justify-start">
                <div className="flex items-start gap-2">
                  <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center">
                    <Bot size={16} className="text-white" />
                  </div>
                  <div className="student-card p-3 rounded-2xl rounded-tl-none flex items-center gap-2 text-gray-500 dark:text-gray-300">
                    <Loader2 className="animate-spin" size={16} /> AI 正在思考…
                  </div>
                </div>
              </div>
            )} */}
            <div ref={messagesEndRef} />
          </div>

          <div className="student-panel p-3 border-t border-slate-200/70 dark:border-slate-700/70">
            <div className="max-w-4xl mx-auto mb-2 flex flex-wrap items-center gap-2">
              <label
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium border ${
                  kbUploading
                    ? "cursor-wait opacity-80 border-slate-200 text-slate-500 dark:border-slate-700 dark:text-slate-400"
                    : "cursor-pointer border-blue-200 text-blue-700 bg-blue-50 hover:bg-blue-100 dark:border-blue-800/50 dark:text-blue-300 dark:bg-blue-900/20"
                }`}
              >
                {kbUploading ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Upload size={14} />
                )}
                {kbUploading ? "资料上传中…" : "上传到当前会话"}
                <input
                  type="file"
                  accept=".pdf,.txt,.md"
                  className="hidden"
                  disabled={kbUploading || loading}
                  onChange={handleKbUpload}
                />
              </label>
              <a
                href={myKbHref}
                className="text-xs text-blue-600 dark:text-blue-300 hover:underline"
              >
                去我的资料库上传长期资料
              </a>
            </div>
            <div className="max-w-4xl mx-auto mb-2 space-y-1.5 text-xs">
              <div className="text-slate-500 dark:text-slate-400">
                当前会话资料 {currentSessionTempDocs.length} 份
              </div>
              <div className="flex flex-wrap items-center gap-1.5">
                {currentSessionTempDocs.length === 0 ? (
                  <span className="text-slate-400 dark:text-slate-500">
                    暂无
                  </span>
                ) : (
                  currentSessionTempDocs.slice(0, 4).map((d) => (
                    <span
                      key={d.id}
                      className="inline-flex items-center px-2 py-0.5 rounded-md bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                      title={`${d.source_name} · ${d.status}`}
                    >
                      {d.title}
                      <span className="ml-1 text-[10px] opacity-70">
                        本会话
                      </span>
                    </span>
                  ))
                )}
                {currentSessionTempDocs.length > 4 && (
                  <span className="text-slate-500 dark:text-slate-400">
                    +{currentSessionTempDocs.length - 4}
                  </span>
                )}
              </div>
            </div>
            {kbHint && (
              <p
                className={`max-w-4xl mx-auto mb-2 text-xs ${
                  kbHint.startsWith("上传失败")
                    ? "text-red-600 dark:text-red-400"
                    : "text-slate-600 dark:text-slate-300"
                }`}
              >
                {kbHint}
              </p>
            )}
            <div className="flex flex-wrap gap-2 mb-2">
              {promptTemplates.map((t, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setInput(t.text)}
                  className="px-2 py-1 text-xs rounded-lg bg-blue-50 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300"
                  disabled={loading}
                >
                  {t.name}
                </button>
              ))}
            </div>
            <div className="relative max-w-4xl mx-auto">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder={
                  loading
                    ? "请稍候…"
                    : "输入后与 AI 对话…（Enter 换行，Ctrl/Cmd+Enter 发送）"
                }
                disabled={loading || !sessionId}
                rows={3}
                className="student-input w-full pl-4 pr-14 py-3 rounded-xl disabled:opacity-60 resize-y min-h-[96px]"
              />
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                <button
                  type="button"
                  onClick={handleSend}
                  disabled={loading || !sessionId}
                  className="p-2 rounded-lg bg-blue-600 text-white disabled:bg-gray-400"
                >
                  {loading ? (
                    <Loader2 size={18} className="animate-spin" />
                  ) : (
                    <Send size={18} />
                  )}
                </button>
              </div>
            </div>
            {!sessionId && (
              <p className="text-center text-xs text-amber-600 mt-2">
                请先在左侧选一个会话，或点 + 新建对话
              </p>
            )}
            <p className="text-center text-xs text-gray-400 mt-1">
              重要知识点请自行核对 · 历史均保留在左侧列表
            </p>
          </div>
        </div>
      </div>

      {deleteTargetId != null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="student-panel rounded-2xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              删除这条对话？
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
              将永久删除对话 <strong>#{deleteTargetId}</strong>{" "}
              及其全部聊天记录，<strong>无法恢复</strong>。确定要继续吗？
            </p>
            <div className="flex gap-3 justify-end">
              <button
                type="button"
                className="student-action-secondary px-4 py-2 rounded-lg"
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
    </StudentLayout>
  );
};

export default StudentHome;
