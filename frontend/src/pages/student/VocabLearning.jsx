import React, { useState, useEffect } from 'react';

// 词汇专项学习页
const VocabLearning = () => {
  // 核心数据状态
  const [vocabList, setVocabList] = useState([]);
  // 学习模式切换（闪卡/列表）
  const [mode, setMode] = useState('flashcard');
  // 闪卡模式专属状态
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isCardFlipped, setIsCardFlipped] = useState(false);
  // 收藏状态（存储已收藏的词汇ID）
  const [collectedIds, setCollectedIds] = useState(new Set());
  // 加载状态
  const [loadingVocab, setLoadingVocab] = useState(false);
  const [collecting, setCollecting] = useState(false);
  const [generating, setGenerating] = useState(false);

  // 页面加载时：获取词汇列表（接口1）
  useEffect(() => {
    const getVocabList = async () => {
      setLoadingVocab(true);
      try {
        const res = await fetch('/api/student/vocab/list', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        if (!res.ok) throw new Error('网络请求失败');
        const result = await res.json();
        if (result.code !== 200) throw new Error(result.message || '获取词汇列表失败');
        
        setVocabList(result.data);
        // 初始化已收藏的词汇ID集合
        const initCollected = new Set();
        result.data.forEach(item => {
          if (item.isCollected) initCollected.add(item.id);
        });
        setCollectedIds(initCollected);
      } catch (err) {
        alert(err.message);
        console.error('获取词汇列表错误：', err);
      } finally {
        setLoadingVocab(false);
      }
    };

    getVocabList();
  }, []);

  // 闪卡模式：切换上一个词汇
  const handlePrevCard = () => {
    if (currentCardIndex <= 0) return;
    setCurrentCardIndex(prev => prev - 1);
    setIsCardFlipped(false);
  };

  // 闪卡模式：切换下一个词汇
  const handleNextCard = () => {
    if (currentCardIndex >= vocabList.length - 1) return;
    setCurrentCardIndex(prev => prev + 1);
    setIsCardFlipped(false);
  };

  // 词汇收藏/取消收藏（接口2）
  const handleCollectVocab = async (vocabId) => {
    if (!vocabId) return;
    setCollecting(true);
    const isCollected = collectedIds.has(vocabId);

    try {
      const res = await fetch('/api/student/vocab/collect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          vocabId: vocabId,
          isCollect: !isCollected
        })
      });
      if (!res.ok) throw new Error('网络请求失败');
      const result = await res.json();
      if (result.code !== 200) throw new Error(result.message || '操作失败');
      
      const newCollected = new Set(collectedIds);
      if (isCollected) {
        newCollected.delete(vocabId);
        alert('已取消收藏');
      } else {
        newCollected.add(vocabId);
        alert('收藏成功');
      }
      setCollectedIds(newCollected);
    } catch (err) {
      alert(err.message);
      console.error('收藏操作错误：', err);
    } finally {
      setCollecting(false);
    }
  };

  // AI生成定制词汇表（接口3）
  const handleAIGenerateVocab = async () => {
    setGenerating(true);
    try {
      const res = await fetch('/api/student/vocab/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          level: "A1",
          topic: "日常通用"
        })
      });
      if (!res.ok) throw new Error('网络请求失败');
      const result = await res.json();
      if (result.code !== 200) throw new Error(result.message || '生成词汇表失败');
      
      setVocabList(result.data);
      setCurrentCardIndex(0);
      setIsCardFlipped(false);
      const newCollected = new Set();
      result.data.forEach(item => {
        if (item.isCollected) newCollected.add(item.id);
      });
      setCollectedIds(newCollected);
      alert('AI定制词汇表生成成功！');
    } catch (err) {
      alert(err.message);
      console.error('AI生成词汇表错误：', err);
    } finally {
      setGenerating(false);
    }
  };

  const currentVocab = vocabList[currentCardIndex] || {};

  return (
    <div className="vocab-learning-page">
      <div className="page-header">
        <h1>德语词汇专项学习</h1>
        <div className="mode-switch">
          <button 
            className={mode === 'flashcard' ? 'active' : ''}
            onClick={() => setMode('flashcard')}
            disabled={loadingVocab}
          >
            闪卡模式
          </button>
          <button 
            className={mode === 'list' ? 'active' : ''}
            onClick={() => setMode('list')}
            disabled={loadingVocab}
          >
            列表模式
          </button>
        </div>
      </div>

      {loadingVocab ? (
        <div className="loading-box">
          <p>加载词汇列表中...</p>
        </div>
      ) : (
        <>
          {mode === 'flashcard' && vocabList.length > 0 && (
            <div className="flashcard-container">
              <div 
                className={`flashcard ${isCardFlipped ? 'flipped' : ''}`}
                onClick={() => setIsCardFlipped(!isCardFlipped)}
              >
                {!isCardFlipped ? (
                  <>
                    <h2>{currentVocab.german}</h2>
                    <p className="hint">点击显示释义</p>
                  </>
                ) : (
                  <>
                    <h2>{currentVocab.chinese}</h2>
                    <p className="example">{currentVocab.example}</p>
                    <p className="hint">点击返回单词</p>
                  </>
                )}
              </div>
              <div className="flashcard-controls">
                <button onClick={handlePrevCard} disabled={currentCardIndex <= 0}>
                  上一个
                </button>
                <button onClick={handleNextCard} disabled={currentCardIndex >= vocabList.length - 1}>
                  下一个
                </button>
                <button 
                  onClick={() => handleCollectVocab(currentVocab.id)}
                  disabled={collecting}
                >
                  {collectedIds.has(currentVocab.id) ? '已收藏' : '加入收藏'}
                </button>
              </div>
            </div>
          )}

          {mode === 'list' && (
            <div className="vocab-list">
              {vocabList.length === 0 ? (
                <p className="empty-tip">暂无词汇数据，点击下方按钮生成词汇表</p>
              ) : (
                vocabList.map(item => (
                  <div key={item.id} className="vocab-item">
                    <div className="german-word">{item.german}</div>
                    <div className="chinese-mean">{item.chinese}</div>
                    <div className="example-sentence">{item.example}</div>
                    <button 
                      className={`collect-btn ${collectedIds.has(item.id) ? 'collected' : ''}`}
                      onClick={() => handleCollectVocab(item.id)}
                      disabled={collecting}
                    >
                      {collectedIds.has(item.id) ? '已收藏' : '收藏'}
                    </button>
                  </div>
                ))
              )}
            </div>
          )}
        </>
      )}

      <div className="ai-generate-section">
        <button 
          className="ai-btn" 
          onClick={handleAIGenerateVocab}
          disabled={generating || loadingVocab}
        >
          {generating ? '生成中...' : '🤖 AI生成定制词汇表'}
        </button>
      </div>
    </div>
  );
};

export default VocabLearning;