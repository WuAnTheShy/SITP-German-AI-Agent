import React, { useState } from 'react';

const WritingAssistant = () => {
  const [userText, setUserText] = useState('');
  const [correctionResult, setCorrectionResult] = useState(null);
  const [sampleEssay, setSampleEssay] = useState('');
  const [isChecking, setIsChecking] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleCheckGrammar = async () => {
    if (!userText.trim()) {
      alert("请先输入德语文本哦！");
      return;
    }

    setIsChecking(true);
    setCorrectionResult(null);
    try {
      const response = await fetch('/api/student/writing/check', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userText: userText.trim()
        })
      });

      const res = await response.json();

      if (res.code === 200) {
        setCorrectionResult(res.data);
      } else {
        alert(res.message || "语法检查失败，请稍后重试");
      }
    } catch (error) {
      console.error("语法检查接口请求异常：", error);
      alert("接口请求失败，请检查网络或联系后端同学");
    } finally {
      setIsChecking(false);
    }
  };

  const handleGenerateSample = async () => {
    if (!userText.trim()) {
      alert("请先输入主题或开头文本哦！");
      return;
    }

    setIsGenerating(true);
    setSampleEssay('');
    try {
      const response = await fetch('/api/student/writing/generate-sample', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userText: userText.trim()
        })
      });

      const res = await response.json();

      if (res.code === 200) {
        setSampleEssay(res.data.sampleEssay);
      } else {
        alert(res.message || "范文生成失败，请稍后重试");
      }
    } catch (error) {
      console.error("范文生成接口请求异常：", error);
      alert("接口请求失败，请检查网络或联系后端同学");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="writing-assistant-page">
      <div className="page-header">
        <h1>AI德语写作辅助</h1>
        <p>实时语法检查、智能润色、范文生成，轻松搞定德语写作</p>
      </div>

      <div className="input-section">
        <textarea
          placeholder="请输入你的德语作文、句子或主题..."
          value={userText}
          onChange={(e) => setUserText(e.target.value)}
          rows={8}
          disabled={isChecking || isGenerating}
        />
        <div className="action-buttons">
          <button 
            className="check-btn" 
            onClick={handleCheckGrammar}
            disabled={isChecking || isGenerating}
          >
            {isChecking ? "🔄 检查中..." : "🤖 检查语法并润色"}
          </button>
          <button 
            className="sample-btn" 
            onClick={handleGenerateSample}
            disabled={isChecking || isGenerating}
          >
            {isGenerating ? "🔄 生成中..." : "📝 AI生成范文"}
          </button>
        </div>
      </div>

      {correctionResult && (
        <div className="result-section">
          <h3>✅ AI批改结果</h3>
          <div className="errors-list">
            <h4>发现的问题：</h4>
            {correctionResult.errors.map((err, index) => (
              <div key={index} className="error-item">
                <span className="position">{err.position}</span>
                <span className="error">{err.error}</span>
                <span className="suggestion">建议：{err.suggestion}</span>
              </div>
            ))}
          </div>
          <div className="polished-text">
            <h4>润色后的文本：</h4>
            <p>{correctionResult.polishedText}</p>
          </div>
        </div>
      )}

      {sampleEssay && (
        <div className="sample-section">
          <h3>📄 AI生成范文</h3>
          <p>{sampleEssay}</p>
        </div>
      )}
    </div>
  );
};

export default WritingAssistant;