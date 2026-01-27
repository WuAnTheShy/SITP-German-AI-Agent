import React, { useState } from 'react';

const ListeningSpeaking = () => {
  // 模拟听力材料列表
  const [listeningMaterials, setListeningMaterials] = useState([
    { id: 1, title: "校园日常对话", level: "A1", duration: "2:30" },
    { id: 2, title: "德国美食介绍", level: "A2", duration: "3:15" },
    { id: 3, title: "留学申请面试", level: "B1", duration: "4:00" },
  ]);

  // 模拟当前选中的听力材料
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  // 口语练习状态
  const [recording, setRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);

  // 选择听力材料
  const handleSelectMaterial = (material) => {
    setSelectedMaterial(material);
  };

  // 开始/结束录音
  const toggleRecording = () => {
    if (recording) {
      setRecording(false);
      // 模拟录音结束生成音频链接
      setAudioUrl("https://example.com/recording.mp3");
    } else {
      setRecording(true);
      setAudioUrl(null);
    }
  };

  // AI口语评分
  const handleAIEvaluation = () => {
    alert("AI正在分析你的发音和语调，稍等...");
  };

  return (
    <div className="listening-speaking-page">
      <div className="page-header">
        <h1>德语听说训练</h1>
        <p>听力磨耳朵 + 口语AI纠音，提升德语实战能力</p >
      </div>

      {/* 听力材料选择区 */}
      <div className="material-selector">
        {listeningMaterials.map(material => (
          <div
            key={material.id}
            className={`material-card ${selectedMaterial?.id === material.id ? 'active' : ''}`}
            onClick={() => handleSelectMaterial(material)}
          >
            <h3>{material.title}</h3>
            <div className="meta">
              <span>难度：{material.level}</span>
              <span>时长：{material.duration}</span>
            </div>
          </div>
        ))}
      </div>

      {/* 听力播放区 */}
      {selectedMaterial && (
        <div className="practice-section">
          <h2>当前练习：{selectedMaterial.title}</h2>
          <div className="listening-player">
            <button className="play-btn">▶️ 播放听力</button>
            <button className="replay-btn">🔄 重新播放</button>
          </div>

          {/* 口语模仿区 */}
          <div className="speaking-area">
            <h3>🎤 模仿口语练习</h3>
            <p>听完后，点击下方按钮开始录音，模仿刚才的内容</p >
            <button
              className={`record-btn ${recording ? 'recording' : ''}`}
              onClick={toggleRecording}
            >
              {recording ? '⏹️ 结束录音' : '🎙️ 开始录音'}
            </button>

            {audioUrl && (
              <div className="audio-preview">
                <h4>你的录音：</h4>
                <audio src={audioUrl} controls />
                <button className="ai-eval-btn" onClick={handleAIEvaluation}>
                  🤖 AI口语评分
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ListeningSpeaking;
