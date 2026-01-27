import React, { useState } from 'react';

const ErrorBookReview = () => {
  // 模拟错题分类（按题型）
  const [errorCategories, setErrorCategories] = useState([
    { id: 1, name: "词汇题", count: 8 },
    { id: 2, name: "语法题", count: 12 },
    { id: 3, name: "翻译题", count: 5 },
    { id: 4, name: "听力题", count: 7 },
  ]);
  // 当前选中的错题分类、对应错题列表
  const [selectedCate, setSelectedCate] = useState(null);
  const [errorList, setErrorList] = useState([
    {
      id: 101,
      question: "选择正确的介词：Ich gehe ____ Schule.",
      userAnswer: "in",
      correctAnswer: "zur",
      analysis: "固定搭配：gehen zur Schule（去上学），Schule为阴性名词，zur=zu+der",
      source: "语法专题练习-介词搭配"
    },
    {
      id: 102,
      question: "翻译：我喜欢读德语书。",
      userAnswer: "Ich mag lese deutsche Bücher.",
      correctAnswer: "Ich mag es, deutsche Bücher zu lesen.",
      analysis: "德语中mag后接带zu的不定式，需加形式宾语es",
      source: "AI写作辅助-翻译练习"
    },
    {
      id: 103,
      question: "写出fahren的第一人称单数现在时",
      userAnswer: "fahr",
      correctAnswer: "fahre",
      analysis: "强变化动词fahren，第一人称单数变位为fahre，需加词尾e",
      source: "语法专题练习-动词变位"
    }
  ]);
  // 复习模式切换
  const [reviewMode, setReviewMode] = useState('browse'); // browse-浏览错题  review-开始复习

  // 选择错题分类
  const handleSelectCate = (cate) => {
    setSelectedCate(cate);
    setReviewMode('browse'); // 切换分类重置为浏览模式
  };

  // 开始针对性复习
  const handleStartReview = () => {
    if (!selectedCate) {
      alert("请先选择一个错题分类再开始复习！");
      return;
    }
    setReviewMode('review');
    alert(`已开启【${selectedCate.name}】针对性复习，AI将生成同类练习题！`);
  };

  // 移除错题
  const handleRemoveError = (id) => {
    setErrorList(prev => prev.filter(item => item.id !== id));
    // 模拟分类数量减少
    setErrorCategories(prev => prev.map(cate => 
      cate.id === selectedCate.id ? { ...cate, count: cate.count - 1 } : cate
    ));
  };

  // 标记已掌握
  const handleMastered = (id) => {
    handleRemoveError(id);
    alert("已标记为掌握，错题已移除！");
  };

  return (
    <div className="error-book-review-page">
      <div className="page-header">
        <h1>德语错题本与复习</h1>
        <p>收集所有错题，AI针对性生成复习计划，精准补漏</p >
      </div>

      {/* 错题分类选择区 */}
      <div className="error-cate-selector">
        {errorCategories.map(cate => (
          <button
            key={cate.id}
            className={selectedCate?.id === cate.id ? 'active' : ''}
            onClick={() => handleSelectCate(cate)}
          >
            {cate.name}
            <span className="error-count">({cate.count}道)</span>
          </button>
        ))}
      </div>

      {/* 错题操作区 */}
      {selectedCate && (
        <div className="error-action">
          <button 
            className="review-btn" 
            onClick={handleStartReview}
            disabled={reviewMode === 'review'}
          >
            🤖 开始AI针对性复习
          </button>
          <p className="mode-tip">当前模式：{reviewMode === 'browse' ? '错题浏览' : '专项复习'}</p >
        </div>
      )}

      {/* 错题列表区 */}
      {selectedCate ? (
        <div className="error-list-section">
          <h2>【{selectedCate.name}】错题列表</h2>
          {errorList.length === 0 ? (
            <div className="no-error-tip">该分类暂无错题，继续保持！🎉</div>
          ) : (
            <div className="error-list">
              {errorList.map(error => (
                <div key={error.id} className="error-item">
                  <div className="error-source">{error.source}</div>
                  <p className="error-question">{error.question}</p >
                  <div className="answer-group">
                    <p><span className="label">你的答案：</span>{error.userAnswer}</p >
                    <p><span className="label correct">正确答案：</span>{error.correctAnswer}</p >
                  </div>
                  <p className="error-analysis"><span className="label">解析：</span>{error.analysis}</p >
                  <div className="error-btns">
                    <button onClick={() => handleMastered(error.id)}>标记已掌握</button>
                    <button onClick={() => handleRemoveError(error.id)} className="remove-btn">删除错题</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="no-cate-tip">请选择一个错题分类，查看你的错题详情吧！</div>
      )}
    </div>
  );
};

export default ErrorBookReview;
