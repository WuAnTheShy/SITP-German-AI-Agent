import React, { useState, useRef, useEffect, useCallback } from "react";
import StudentLayout from "../../components/StudentLayout";
import request from "../../api/request";
import {
  API_SCENE_CHAT,
  API_SCENE_CHAT_STATE,
  API_SCENE_CHAT_CLEAR,
} from "../../api/config";
import { Bot, User, Send, Loader2, Trash2 } from "lucide-react";

const WELCOME = (name) =>
  `你好！现在进入【${name}】场景，开始用德语对话吧～我会纠正你的表达错误哦！（本情景一条连续对话，会自动接续上次练习）`;

function mapServerMessagesToUi(rows) {
  if (!Array.isArray(rows) || rows.length === 0) return [];
  const out = [];
  for (const m of rows) {
    if (m.role === "user") {
      out.push({
        key: `u-${m.id}`,
        sender: "我",
        content: m.content,
        time: "",
      });
    } else {
      out.push({
        key: `a-${m.id}`,
        sender: "AI",
        content: m.content,
        time: "",
      });
      if (m.correction) {
        out.push({
          key: `c-${m.id}`,
          sender: "系统",
          content: `📝 语法纠错建议：${m.correction}`,
          time: "",
        });
      }
    }
  }
  return out;
}

const AISceneChat = () => {
  const [chatScenes] = useState([
    { id: 1, name: "校园课堂问答", desc: "和老师互动、回答课堂问题" },
    { id: 2, name: "日常购物交流", desc: "超市/商店买东西的德语对话" },
    { id: 3, name: "留学面试沟通", desc: "德国大学入学面试常见问题" },
    { id: 4, name: "餐厅点餐对话", desc: "德国餐厅点餐、询问菜品" },
  ]);
  const [selectedScene, setSelectedScene] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMsg, setInputMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingScene, setLoadingScene] = useState(false);
  const chatContainerRef = useRef(null);
  const inputRef = useRef(null);

  const loadSceneState = useCallback(async (scene) => {
    if (!scene) return;
    setLoadingScene(true);
    try {
      const r = await request.get(API_SCENE_CHAT_STATE, {
        params: { scene_id: scene.id, scene_name: scene.name },
      });
      const payload = r.data?.data ?? r.data ?? {};
      const msgs = payload.messages ?? [];
      const ui = mapServerMessagesToUi(msgs);
      if (ui.length === 0) {
        setMessages([
          {
            key: "welcome",
            sender: "AI",
            content: WELCOME(scene.name),
            time: new Date().toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            }),
          },
        ]);
      } else {
        setMessages(ui);
      }
    } catch (e) {
      console.error(e);
      setMessages([
        {
          key: "err",
          sender: "系统",
          content: "加载记录失败，请刷新重试。",
          time: "",
        },
      ]);
    } finally {
      setLoadingScene(false);
    }
  }, []);

  const handleSelectScene = (scene) => {
    setSelectedScene(scene);
    loadSceneState(scene);
  };

  const handleClearScene = async () => {
    if (!selectedScene) return;
    if (
      !window.confirm(
        "确定清空本情景的全部对话记录？不可恢复，清空后从新对话开始。"
      )
    )
      return;
    try {
      await request.delete(API_SCENE_CHAT_CLEAR, {
        params: {
          scene_id: selectedScene.id,
          scene_name: selectedScene.name,
        },
      });
      loadSceneState(selectedScene);
    } catch (e) {
      console.error(e);
      alert("清空失败");
    }
  };

  const handleSendMsg = async () => {
    if (!inputMsg.trim() || !selectedScene) {
      alert(selectedScene ? "请输入德语对话内容！" : "请先选择一个对话场景！");
      return;
    }
    const userContent = inputMsg.trim();
    setMessages((prev) => [
      ...prev,
      {
        key: `local-${Date.now()}`,
        sender: "我",
        content: userContent,
        time: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      },
    ]);
    setInputMsg("");
    setLoading(true);
    try {
      const response = await request.post(
        API_SCENE_CHAT,
        {
          sceneId: selectedScene.id,
          sceneName: selectedScene.name,
          userMessage: userContent,
        },
        { timeout: 60000 }
      );
      const data = response.data;
      const payload = data.data ?? data;
      const code = data.code;
      if (code === 200 || payload?.reply != null) {
        setMessages((prev) => [
          ...prev,
          {
            key: `ai-${Date.now()}`,
            sender: "AI",
            content: payload.reply,
            time: new Date().toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            }),
          },
        ]);
        if (payload.correction) {
          setMessages((prev) => [
            ...prev,
            {
              key: `sys-${Date.now()}`,
              sender: "系统",
              content: `📝 语法纠错建议：${payload.correction}`,
              time: new Date().toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              }),
            },
          ]);
        }
      } else {
        throw new Error(data.message || "请求失败，请重试");
      }
    } catch (error) {
      console.error("接口请求失败:", error);
      setMessages((prev) => [
        ...prev,
        {
          key: `err-${Date.now()}`,
          sender: "系统",
          content: `❌ ${error.message || "网络错误"}`,
          time: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !loading) handleSendMsg();
  };

  useEffect(() => {
    if (!loading) inputRef.current?.focus();
  }, [loading]);

  useEffect(() => {
    if (chatContainerRef.current)
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
  }, [messages, loading]);

  return (
    <StudentLayout>
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <h1 className="text-xl font-bold text-gray-800 dark:text-gray-200 mb-4">
            🗣️ 场景化AI德语对话
          </h1>
          <div className="flex gap-3 flex-wrap">
            {chatScenes.map((scene) => (
              <button
                key={scene.id}
                onClick={() => handleSelectScene(scene)}
                className={`px-4 py-3 rounded-lg border-2 text-left transition-all ${
                  selectedScene?.id === scene.id
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400"
                    : "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-blue-300 text-gray-700 dark:text-gray-300"
                }`}
              >
                <strong className="block text-sm">{scene.name}</strong>
                <span className="text-xs opacity-70">{scene.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {selectedScene ? (
          <>
            <div className="px-4 py-1.5 border-b border-gray-100 dark:border-gray-800 flex justify-end">
              <button
                type="button"
                title="清空本情景对话记录"
                aria-label="清空本情景"
                onClick={handleClearScene}
                disabled={loadingScene}
                className="p-2 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-40"
              >
                <Trash2 size={20} />
              </button>
            </div>
            {loadingScene ? (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                <Loader2 className="animate-spin mr-2" /> 加载记录…
              </div>
            ) : (
              <>
                <div
                  className="flex-1 overflow-y-auto p-6 space-y-4"
                  ref={chatContainerRef}
                >
                  {messages.map((msg) => (
                    <div
                      key={msg.key}
                      className={`flex ${
                        msg.sender === "我" ? "justify-end" : "justify-start"
                      }`}
                    >
                      <div
                        className={`flex items-start gap-3 max-w-xl ${
                          msg.sender === "我" ? "flex-row-reverse" : ""
                        }`}
                      >
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                            msg.sender === "我"
                              ? "bg-blue-600"
                              : msg.sender === "系统"
                                ? "bg-yellow-500"
                                : "bg-green-600"
                          }`}
                        >
                          {msg.sender === "我" ? (
                            <User size={14} className="text-white" />
                          ) : (
                            <Bot size={14} className="text-white" />
                          )}
                        </div>
                        <div>
                          <div
                            className={`p-3 rounded-2xl whitespace-pre-wrap ${
                              msg.sender === "我"
                                ? "bg-blue-600 text-white rounded-tr-none"
                                : msg.sender === "系统"
                                  ? "bg-yellow-50 border border-yellow-200 text-yellow-800 dark:text-yellow-200 rounded-tl-none"
                                  : "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm dark:shadow-gray-900/50 rounded-tl-none text-gray-800 dark:text-white"
                            }`}
                          >
                            {msg.content}
                          </div>
                          {msg.time ? (
                            <span className="text-xs text-gray-400 dark:text-gray-500 mt-1 block">
                              {msg.time}
                            </span>
                          ) : null}
                        </div>
                      </div>
                    </div>
                  ))}
                  {loading && (
                    <div className="flex justify-start">
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center">
                          <Bot size={14} className="text-white" />
                        </div>
                        <div className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm dark:shadow-gray-900/50 rounded-2xl rounded-tl-none text-gray-500 dark:text-white flex items-center gap-2">
                          <Loader2 className="animate-spin" size={16} />{" "}
                          AI正在思考...
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <div className="p-4 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
                  <div className="max-w-3xl mx-auto flex gap-3">
                    <input
                      ref={inputRef}
                      type="text"
                      placeholder={
                        loading
                          ? "AI正在回复，请稍候..."
                          : "请输入德语内容（按回车发送）..."
                      }
                      value={inputMsg}
                      onChange={(e) => setInputMsg(e.target.value)}
                      onKeyDown={handleKeyDown}
                      disabled={loading}
                      className="dark:text-white flex-1 px-4 py-3 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white dark:bg-gray-800 disabled:bg-gray-100 dark:bg-gray-800"
                    />
                    <button
                      onClick={handleSendMsg}
                      disabled={loading}
                      className={`px-5 py-3 rounded-xl font-medium transition-colors ${
                        loading
                          ? "bg-gray-400 cursor-not-allowed text-white"
                          : "bg-blue-600 hover:bg-blue-700 text-white"
                      }`}
                    >
                      {loading ? (
                        <Loader2 size={18} className="animate-spin" />
                      ) : (
                        <Send size={18} />
                      )}
                    </button>
                  </div>
                </div>
              </>
            )}
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-400 dark:text-gray-500 text-lg">
            请在上方选择一个对话场景，开启你的德语口语练习吧！
          </div>
        )}
      </div>
    </StudentLayout>
  );
};

export default AISceneChat;
