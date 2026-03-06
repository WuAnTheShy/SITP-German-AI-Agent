import React, { useState, useEffect } from 'react';
import StudentLayout from '../../components/StudentLayout';
import request from '../../api/request';
import { API_VOCAB_LIST, API_VOCAB_COLLECT, API_VOCAB_GENERATE } from '../../api/config';

const VocabLearning = () => {
  const [vocabList, setVocabList] = useState([]);
  const [mode, setMode] = useState('flashcard');
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isCardFlipped, setIsCardFlipped] = useState(false);
  const [collectedIds, setCollectedIds] = useState(new Set());
  const [loadingVocab, setLoadingVocab] = useState(false);
  const [collecting, setCollecting] = useState(false);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    const getVocabList = async () => {
      setLoadingVocab(true);
      try {
        const response = await request.get(API_VOCAB_LIST);
        const result = response.data;
        if (result.code !== 200) throw new Error(result.message || '获取词汇列表失败');
        setVocabList(result.data);
        const initCollected = new Set();
        result.data.forEach(item => { if (item.isCollected) initCollected.add(item.id); });
        setCollectedIds(initCollected);
      } catch (err) { alert(err.message); }
      finally { setLoadingVocab(false); }
    };
    getVocabList();
  }, []);

  const handlePrevCard = () => { if (currentCardIndex > 0) { setCurrentCardIndex(prev => prev - 1); setIsCardFlipped(false); } };
  const handleNextCard = () => { if (currentCardIndex < vocabList.length - 1) { setCurrentCardIndex(prev => prev + 1); setIsCardFlipped(false); } };

  const handleCollectVocab = async (vocabId) => {
    if (!vocabId) return;
    setCollecting(true);
    const isCollected = collectedIds.has(vocabId);
    try {
      const response = await request.post(API_VOCAB_COLLECT, { vocabId, isCollect: !isCollected });
      const result = response.data;
      if (result.code !== 200) throw new Error(result.message || '操作失败');
      const newCollected = new Set(collectedIds);
      if (isCollected) { newCollected.delete(vocabId); } else { newCollected.add(vocabId); }
      setCollectedIds(newCollected);
    } catch (err) { alert(err.message); }
    finally { setCollecting(false); }
  };

  const handleAIGenerateVocab = async () => {
    setGenerating(true);
    try {
      const response = await request.post(API_VOCAB_GENERATE, { level: "A1", topic: "日常通用" });
      const result = response.data;
      if (result.code !== 200) throw new Error(result.message || '生成词汇表失败');
      setVocabList(result.data);
      setCurrentCardIndex(0); setIsCardFlipped(false);
      const newCollected = new Set();
      result.data.forEach(item => { if (item.isCollected) newCollected.add(item.id); });
      setCollectedIds(newCollected);
      alert('AI定制词汇表生成成功！');
    } catch (err) { alert(err.message); }
    finally { setGenerating(false); }
  };

  const currentVocab = vocabList[currentCardIndex] || {};

  return (
    <StudentLayout>
      <div className="flex-1 overflow-y-auto p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-200 mb-2">📚 德语词汇专项学习</h1>
            <p className="text-gray-500 dark:text-gray-400">闪卡记忆 + 列表浏览，高效掌握德语词汇</p>
          </div>
          <div className="flex gap-2 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
            <button onClick={() => setMode('flashcard')} disabled={loadingVocab}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${mode === 'flashcard' ? 'bg-white dark:bg-gray-800 shadow text-blue-700 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:text-gray-200'}`}>
              闪卡模式
            </button>
            <button onClick={() => setMode('list')} disabled={loadingVocab}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${mode === 'list' ? 'bg-white dark:bg-gray-800 shadow text-blue-700 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:text-gray-200'}`}>
              列表模式
            </button>
          </div>
        </div>

        {loadingVocab ? (
          <div className="text-center py-16 text-gray-400 dark:text-gray-500">加载词汇列表中...</div>
        ) : (
          <>
            {/* 闪卡模式 */}
            {mode === 'flashcard' && vocabList.length > 0 && (
              <div className="flex flex-col items-center">
                <div onClick={() => setIsCardFlipped(!isCardFlipped)}
                  className="w-96 h-56 bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 flex flex-col items-center justify-center cursor-pointer hover:shadow-xl transition-shadow p-8 select-none">
                  {!isCardFlipped ? (
                    <>
                      <h2 className="text-3xl font-bold text-gray-800 dark:text-gray-200 mb-3">{currentVocab.german}</h2>
                      <p className="text-sm text-gray-400 dark:text-gray-500">点击显示释义</p>
                    </>
                  ) : (
                    <>
                      <h2 className="text-2xl font-bold text-blue-700 dark:text-blue-400 mb-2">{currentVocab.chinese}</h2>
                      <p className="text-sm text-gray-600 dark:text-gray-400 italic">{currentVocab.example}</p>
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">点击返回单词</p>
                    </>
                  )}
                </div>
                <div className="flex gap-3 mt-6">
                  <button onClick={handlePrevCard} disabled={currentCardIndex <= 0}
                    className="px-5 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">上一个</button>
                  <span className="px-4 py-2 text-gray-500 dark:text-gray-400 text-sm">{currentCardIndex + 1} / {vocabList.length}</span>
                  <button onClick={handleNextCard} disabled={currentCardIndex >= vocabList.length - 1}
                    className="px-5 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">下一个</button>
                  <button onClick={() => handleCollectVocab(currentVocab.id)} disabled={collecting}
                    className={`px-5 py-2 rounded-lg transition-colors ${collectedIds.has(currentVocab.id) ? 'bg-yellow-100 text-yellow-700' : 'bg-blue-100 text-blue-700 dark:text-blue-400 hover:bg-blue-200'} disabled:opacity-50`}>
                    {collectedIds.has(currentVocab.id) ? '⭐ 已收藏' : '☆ 加入收藏'}
                  </button>
                </div>
              </div>
            )}

            {/* 列表模式 */}
            {mode === 'list' && (
              <div className="space-y-3">
                {vocabList.length === 0 ? (
                  <p className="text-center text-gray-400 dark:text-gray-500 py-8">暂无词汇数据，点击下方按钮生成词汇表</p>
                ) : vocabList.map(item => (
                  <div key={item.id} className="flex items-center gap-4 p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 hover:shadow-sm dark:shadow-gray-900/50 transition-shadow">
                    <div className="font-bold text-lg text-gray-800 dark:text-gray-200 w-40">{item.german}</div>
                    <div className="text-gray-600 dark:text-gray-400 w-32">{item.chinese}</div>
                    <div className="flex-1 text-sm text-gray-500 dark:text-gray-400 italic">{item.example}</div>
                    <button onClick={() => handleCollectVocab(item.id)} disabled={collecting}
                      className={`px-4 py-2 rounded-lg text-sm transition-colors shrink-0 ${collectedIds.has(item.id) ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-blue-100 hover:text-blue-700 dark:text-blue-400'}`}>
                      {collectedIds.has(item.id) ? '⭐ 已收藏' : '收藏'}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* AI生成 */}
        <div className="mt-8 text-center">
          <button onClick={handleAIGenerateVocab} disabled={generating || loadingVocab}
            className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium text-lg">
            {generating ? '生成中...' : '🤖 AI生成定制词汇表'}
          </button>
        </div>
      </div>
    </StudentLayout>
  );
};

export default VocabLearning;
