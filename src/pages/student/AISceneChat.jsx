import React, { useState, useRef, useEffect } from 'react';

const AISceneChat = () => {
  // 1. 场景定义（保持不变）
  const [chatScenes] = useState([
    { id: 1, name: "校园课堂问答", desc: "和老师互动、回答课堂问题" },
    { id: 2, name: "日常购物交流", desc: "超市/商店买东西的德语对话" },
    { id: 3, name: "留学面试沟通", desc: "德国大学入学面试常见问题" },
    { id: 4, name: "餐厅点餐对话", desc: "德国餐厅点餐、询问菜品" },
  ]);

  // 2. 状态管理
  const [selectedScene, setSelectedScene] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMsg, setInputMsg] = useState('');
  const [loading, setLoading] = useState(false); // 新增：加载状态
  
  const chatContainerRef = useRef(null);

  // 3. 选择场景
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

  // 4. 发送消息（核心修改部分！）
  const handleSendMsg = async () => {
    if (!inputMsg.trim() || !selectedScene) {
      alert(selectedScene ? "请输入德语对话内容！" : "请先选择一个对话场景！");
      return;
    }

    // (1) 立即显示用户的消息
    const userContent = inputMsg;
    const newUserMsg = {
      sender: "我",
      content: userContent,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    
    setMessages(prev => [...prev, newUserMsg]);
    setInputMsg(''); // 清空输入框
    setLoading(true); // 开始转圈圈

    try {
      // (2) 拼装发给 AI 的内容，带上场景信息，让 AI 更入戏
      // 比如发送： "[当前场景：餐厅点餐] 我想要一杯啤酒"
      const promptToSend = `[当前场景：${selectedScene.name}] ${userContent}`;

      // (3) 调用你的 Python 后端
      const response = await fetch('https://sitp-german-ai-agent-1.onrender.com', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: promptToSend }),
      });

      const data = await response.json();

      // (4) 显示 AI 的真实回复
      const newAiMsg = {
        sender: "AI",
        content: data.reply, // 后端返回的真实字段
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, newAiMsg]);

    } catch (error) {
      console.error("请求失败:", error);
      // 如果报错，显示错误提示
      setMessages(prev => [...prev, {
        sender: "系统",
        content: "❌ 连接后端失败，请确认黑色终端窗口没有关闭！",
        time: new Date().toLocaleTimeString()
      }]);
    } finally {
      setLoading(false); // 结束转圈圈
    }
  };

  // 5. 按回车发送
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !loading) handleSendMsg();
  };

  // 6. 自动滚动到底部
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, loading]);

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
            <span className="scene-desc" style={{display:'block', fontSize:'0.8em', opacity:0.8}}>{scene.desc}</span>
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
              disabled={loading} // 发送中禁止输入
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
        <div className="no-scene-tip" style={{textAlign:'center', padding:'40px', color:'#666'}}>
          请在上方选择一个对话场景，开启你的德语口语练习吧！
        </div>
      )}
    </div>
  );
};

export default AISceneChat;