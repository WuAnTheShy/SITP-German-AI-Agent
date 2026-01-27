import React, { useState } from 'react';

// 词汇专项学习页
const VocabLearning = () => {
  // 模拟词汇数据
  const [vocabList, setVocabList] = useState([
    { id: 1, german: "Haus", chinese: "房子", example: "Das ist mein Haus." },
    { id: 2, german: "Auto", chinese: "汽车", example: "Ich fahre ein Auto." },
    { id: 3, german: "Buch", chinese: "书", example: "Ich lese ein Buch." },
  ]);

  // 学习模式切换（闪卡/列表）
  const [mode, setMode] = useState('flashcard');

  return (
    <div className="vocab-learning-page">
      <div className="page-header">
        <h1>德语词汇专项学习</h1>
        <div className="mode-switch">
          <button 
            className={mode === 'flashcard' ? 'active' : ''}
            onClick={() => setMode('flashcard')}
          >
            闪卡模式
          </button>
          <button 
            className={mode === 'list' ? 'active' : ''}
            onClick={() => setMode('list')}
          >
            列表模式
          </button>
        </div>
      </div>

      {/* 闪卡模式 */}
      {mode === 'flashcard' && (
        <div className="flashcard-container">
          <div className="flashcard">
            <h2>Haus</h2>
            <p className="hint">点击显示释义</p >
          </div>
          <div className="flashcard-controls">
            <button>上一个</button>
            <button>下一个</button>
            <button>加入收藏</button>
          </div>
        </div>
      )}

      {/* 列表模式 */}
      {mode === 'list' && (
        <div className="vocab-list">
          {vocabList.map(item => (
            <div key={item.id} className="vocab-item">
              <div className="german-word">{item.german}</div>
              <div className="chinese-mean">{item.chinese}</div>
              <div className="example-sentence">{item.example}</div>
              <button className="collect-btn">收藏</button>
            </div>
          ))}
        </div>
      )}

      {/* AI生成词汇表按钮 */}
      <div className="ai-generate-section">
        <button className="ai-btn">
          🤖 AI生成定制词汇表
        </button>
      </div>
    </div>
  );
};

export default VocabLearning;
