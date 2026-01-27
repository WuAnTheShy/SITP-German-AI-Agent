import React, { useState } from 'react';

const WritingAssistant = () => {
  // 用户输入的德语文本
  const [userText, setUserText] = useState('');
  // AI返回的批改结果
  const [correctionResult, setCorrectionResult] = useState(null);
  // AI生成的范文
  const [sampleEssay, setSampleEssay] = useState('');

  // 触发AI语法检查与润色
  const handleCheckGrammar = () => {
    if (!userText.trim()) {
      alert("请先输入德语文本哦！");
      return;
    }
    // 模拟AI返回结果
    setCorrectionResult({
      errors: [
        { position: "第1行第5个词", error: "动词变位错误", suggestion: "将「gehe」改为「gehst」" },
        { position: "第2行第3个词", error: "介词搭配错误", suggestion: "将「in」改为「auf」" }
      ],
      polishedText: "Du gehst zur Schule. Am Wochenende gehe ich ins Kino mit Freunden."
    });
  };

  // 触发AI生成范文
  const handleGenerateSample = () => {
    if (!userText.trim()) {
      alert("请先输入主题或开头文本哦！");
      return;
    }
    // 模拟AI生成范文
    setSampleEssay(
      "Meine Lieblingsaktivität am Wochenende ist, mit Freunden ins Kino zu gehen. " +
      "Gestern haben wir einen deutschen Film gesehen, der sehr spannend war. " +
      "Danach sind wir ins Café gegangen und haben Kaffee getrunken. " +
      "Es war ein toller Tag!"
    );
  };

  return (
    <div className="writing-assistant-page">
      <div className="page-header">
        <h1>AI德语写作辅助</h1>
        <p>实时语法检查、智能润色、范文生成，轻松搞定德语写作</p >
      </div>

      {/* 写作输入区 */}
      <div className="input-section">
        <textarea
          placeholder="请输入你的德语作文、句子或主题..."
          value={userText}
          onChange={(e) => setUserText(e.target.value)}
          rows={8}
        />
        <div className="action-buttons">
          <button className="check-btn" onClick={handleCheckGrammar}>
            🤖 检查语法并润色
          </button>
          <button className="sample-btn" onClick={handleGenerateSample}>
            📝 AI生成范文
          </button>
        </div>
      </div>

      {/* AI批改结果区 */}
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
            <p>{correctionResult.polishedText}</p >
          </div>
        </div>
      )}

      {/* AI范文展示区 */}
      {sampleEssay && (
        <div className="sample-section">
          <h3>📄 AI生成范文</h3>
          <p>{sampleEssay}</p >
        </div>
      )}
    </div>
  );
};

export default WritingAssistant;
