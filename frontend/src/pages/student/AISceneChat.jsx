import React, { useState, useRef, useEffect } from 'react';
import { API_BASE } from '../../api/config';

// 接口基础配置：统一管理后端地址，后续后端部署后只改这里就行
const API_BASE_URL = API_BASE;
// 场景对话接口地址（和上面的规范完全一致，绝对不能改）
const SCENE_CHAT_API = `${API_BASE_URL}/api/student/scene-chat`;

const AISceneChat = () => {
    // 1. 场景定义（完全保留你原来的内容，没动）
    const [chatScenes] = useState([
        { id: 1, name: "校园课堂问答", desc: "和老师互动、回答课堂问题" },
        { id: 2, name: "日常购物交流", desc: "超市/商店买东西的德语对话" },
        { id: 3, name: "留学面试沟通", desc: "德国大学入学面试常见问题" },
        { id: 4, name: "餐厅点餐对话", desc: "德国餐厅点餐、询问菜品" }
    ]);

    // 2. 状态管理（完全保留你原来的内容，没动）
    const [selectedScene, setSelectedScene] = useState(null);
    const [messages, setMessages] = useState([]);
    const [inputMsg, setInputMsg] = useState('');
    const [loading, setLoading] = useState(false);
    const chatContainerRef = useRef(null);

    // 3. 选择场景（完全保留你原来的内容，没动）
    const handleSelectScene = (scene) => {
        setSelectedScene(scene);
        setMessages([
            {
                sender: "AI",
                content: `你好！现在进入【${scene.name}】场景，开始用德语对话吧～我会纠正你的表达错误哦！`,
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }
        ]);
    };

    // 4. 发送消息（核心接口逻辑，全部按规范重写完成）
    const handleSendMsg = async () => {
        if (!inputMsg.trim() || !selectedScene) {
            alert(selectedScene ? "请输入德语对话内容！" : "请先选择一个对话场景！");
            return;
        }

        // 立即显示用户的消息（完全保留原来的逻辑）
        const userContent = inputMsg.trim();
        const newUserMsg = {
            sender: "我",
            content: userContent,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };

        setMessages(prev => [...prev, newUserMsg]);
        setInputMsg('');
        setLoading(true);

        try {
            // 【接口核心1】按规范拼装请求参数，发给后端
            const requestData = {
                sceneId: selectedScene.id,
                sceneName: selectedScene.name,
                userMessage: userContent
            };

            // 【接口核心2】发送请求到后端接口
            const response = await fetch(SCENE_CHAT_API, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            // 【接口核心3】解析后端返回的数据
            const data = await response.json();

            // 【接口核心4】判断请求是否成功，按规范处理
            if (data.code === 200) {
                // 成功：显示AI回复
                const newAiMsg = {
                    sender: "AI",
                    content: data.data.reply,
                    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                };
                setMessages(prev => [...prev, newAiMsg]);

                // 可选：如果后端返回了纠错信息，自动显示
                if (data.data.correction) {
                    const correctionMsg = {
                        sender: "系统",
                        content: `📝 语法纠错建议：${data.data.correction}`,
                        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                    };
                    setMessages(prev => [...prev, correctionMsg]);
                }
            } else {
                // 后端返回失败，抛出错误交给catch处理
                throw new Error(data.message || '请求失败，请重试');
            }

        } catch (error) {
            console.error("接口请求失败:", error);
            // 显示错误提示，用户能直接看到
            setMessages(prev => [...prev, {
                sender: "系统",
                content: `❌ ${error.message}`,
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }]);
        } finally {
            // 无论成功失败，都关闭加载状态
            setLoading(false);
        }
    };

    // 5. 按回车发送（完全保留你原来的内容，没动）
    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !loading) {
            handleSendMsg();
        }
    };

    // 6. 自动滚动到底部（完全保留你原来的内容，没动）
    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [messages, loading]);

    // 页面渲染内容（完全保留你原来的布局和样式，没动）
    return (
        <div className="ai-scene-chat-page">
            <div className="page-header">
                <h1>场景化AI德语对话</h1>
                <p>模拟真实场景练口语，AI实时纠错+互动</p>
            </div>

            {/* 场景选择区 */}
            <div className="scene-selector">
                {chatScenes.map(scene => (
                    <button
                        key={scene.id}
                        className={selectedScene?.id === scene.id ? 'active' : ''}
                        onClick={() => handleSelectScene(scene)}
                    >
                        <strong>{scene.name}</strong>
                        <span className="scene-desc" style={{ display: 'block', fontSize: '0.8em', opacity: 0.8 }}>{scene.desc}</span>
                    </button>
                ))}
            </div>

            {/* 对话区域 */}
            {selectedScene ? (
                <div className="chat-section">
                    <div className="chat-header">当前场景：{selectedScene.name}</div>

                    <div className="chat-container" ref={chatContainerRef}>
                        {messages.length === 0 ? (
                            <div className="empty-chat">点击场景开始对话吧～</div>
                        ) : (
                            messages.map((msg, index) => (
                                <div key={index} className={`chat-msg ${msg.sender === '我' ? 'user-msg' : 'ai-msg'}`}>
                                    <div className="msg-sender">{msg.sender}</div>
                                    <div className="msg-content">{msg.content}</div>
                                    <div className="msg-time">{msg.time}</div>
                                </div>
                            ))
                        )}

                        {/* 加载中的提示 */}
                        {loading && (
                            <div className="chat-msg ai-msg">
                                <div className="msg-sender">AI</div>
                                <div className="msg-content">Thinking... (AI正在思考中) 🇩🇪</div>
                            </div>
                        )}
                    </div>

                    {/* 输入框区域 */}
                    <div className="chat-input">
                        <input
                            type="text"
                            placeholder={loading ? "AI正在回复，请稍候..." : "请输入德语内容（按回车发送）..."}
                            value={inputMsg}
                            onChange={(e) => setInputMsg(e.target.value)}
                            onKeyDown={handleKeyDown}
                            disabled={loading}
                        />
                        <button
                            onClick={handleSendMsg}
                            className="send-btn"
                            disabled={loading}
                            style={{ opacity: loading ? 0.5 : 1 }}
                        >
                            {loading ? '发送中...' : '发送 🚀'}
                        </button>
                    </div>
                </div>
            ) : (
                <div className="no-scene-tip" style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
                    请在上方选择一个对话场景，开启你的德语口语练习吧！
                </div>
            )}
        </div>
    );
};

export default AISceneChat;