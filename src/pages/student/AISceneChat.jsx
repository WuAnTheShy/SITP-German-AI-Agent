import React, { useState, useRef, useEffect } from 'react';

const AISceneChat = () => {
  // 模拟德语对话场景（贴合大学/留学/日常核心场景）
  const [chatScenes, setChatScenes] = useState([
    { id: 1, name: "校园课堂问答", desc: "和老师互动、回答课堂问题" },
    { id: 2, name: "日常购物交流", desc: "超市/商店买东西的德语对话" },
    { id: 3, name: "留学面试沟通", desc: "德国大学入学面试常见问题" },
    { id: 4, name: "餐厅点餐对话", desc: "德国餐厅点餐、询问菜品" },
  ]);
  // 当前选中场景、对话消息、输入框内容
  const [selectedScene, setSelectedScene] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMsg, setInputMsg] = useState('');
  // 滚动到底部的ref
  const chatContainerRef = useRef(null);

  // 选择对话场景，初始化AI欢迎语
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

  // 发送用户消息，模拟AI回复
  const handleSendMsg = () => {
    if (!inputMsg.trim() || !selectedScene) {
      alert(selectedScene ? "请输入德语对话内容！" : "请先选择一个对话场景！");
      return;
    }
    // 添加用户消息
    const newUserMsg = {
      sender: "我",
      content: inputMsg,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages(prev => [...prev, newUserMsg]);
    setInputMsg('');

    // 模拟AI延迟回复（带简单纠错提示）
    setTimeout(() => {
      const aiReplys = [
        "你的表达很准确！继续加油～",
        "小错误：这里应该用介词in哦，正确表达是...",
        "很棒！可以再简洁一点，德语中可以说...",
        "注意动词变位：主语是du，动词应该用...形式"
      ];
      const randomReply = aiReplys[Math.floor(Math.random() * aiReplys.length)];
      setMessages(prev => [
        ...prev,
        {
          sender: "AI",
          content: randomReply,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    }, 800);
  };

  // 按回车发送消息
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSendMsg();
  };

  // 对话更新时滚动到底部
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="ai-scene-chat-page">
      <div className="page-header">
        <h1>场景化AI德语对话</h1>
        <p>模拟真实场景练口语，AI实时纠错+互动</p >
      </div>

      {/* 场景选择区 */}
      <div className="scene-selector">
        {chatScenes.map(scene => (
          <button
            key={scene.id}
            className={selectedScene?.id === scene.id ? 'active' : ''}
            onClick={() => handleSelectScene(scene)}
          >
            {scene.name}
            <span className="scene-desc">{scene.desc}</span>
          </button>
        ))}
      </div>

      {/* 对话区域 */}
      {selectedScene ? (
        <div className="chat-section">
          <div className="chat-header">当前场景：{selectedScene.name}</div>
          {/* 对话消息容器 */}
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
          </div>
          {/* 输入框区域 */}
          <div className="chat-input">
            <input
              type="text"
              placeholder="请输入德语内容（按回车发送）..."
              value={inputMsg}
              onChange={(e) => setInputMsg(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button onClick={handleSendMsg} className="send-btn">发送 🚀</button>
          </div>
        </div>
      ) : (
        <div className="no-scene-tip">请选择一个对话场景，开启你的德语口语练习吧！</div>
      )}
    </div>
  );
};

export default AISceneChat;
