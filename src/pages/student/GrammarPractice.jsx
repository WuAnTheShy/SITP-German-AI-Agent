import React, { useState } from 'react';

const GrammarPractice = () => {
  // 模拟语法分类
  const [grammarCategories, setGrammarCategories] = useState([
    { id: 1, name: "现在时", desc: "Präsens" },
    { id: 2, name: "过去时", desc: "Präteritum" },
    { id: 3, name: "完成时", desc: "Perfekt" },
    { id: 4, name: "从句", desc: "Nebensatz" },
  ]);

  // 当前选中的语法点
  const [selectedCategory, setSelectedCategory] = useState(null);
  // 模拟练习题
  const [exercises, setExercises] = useState([
    {
      id: 1,
      question: "Ich ____ (essen) ein Apfel.",
      answer: "esse",
      analysis: "第一人称单数现在时，动词essen的变位为esse"
    },
    {
      id: 2,
      question: "Du ____ (gehen) zur Schule.",
      answer: "gehst",
      analysis: "第二人称单数现在时，动词gehen的变位为gehst"
    }
  ]);
  // 用户输入的答案
  const [userAnswers, setUserAnswers] = useState({});

  // 选择语法分类
  const handleSelectCategory = (category) => {
    setSelectedCategory(category);
  };

  // 提交答案并查看AI解析
  const handleSubmit = () => {
    alert("已提交！AI正在批改解析中...");
  };

  return (
    <div className="grammar-practice-page">
      <div className="page-header">
        <h1>德语语法专题练习</h1>
        <p>选择语法点开始练习，AI将为你解析错题</p >
      </div>

      {/* 语法分类选择区 */}
      <div className="category-selector">
        {grammarCategories.map(category => (
          <button
            key={category.id}
            className={selectedCategory?.id === category.id ? 'active' : ''}
            onClick={() => handleSelectCategory(category)}
          >
            {category.name}
            <span className="desc">{category.desc}</span>
          </button>
        ))}
      </div>

      {/* 练习题区 */}
      {selectedCategory && (
        <div className="exercise-section">
          <h2>当前练习：{selectedCategory.name}</h2>
          <div className="exercise-list">
            {exercises.map(exercise => (
              <div key={exercise.id} className="exercise-item">
                <p className="question">{exercise.question}</p >
                <input
                  type="text"
                  placeholder="请输入答案"
                  value={userAnswers[exercise.id] || ''}
                  onChange={(e) => setUserAnswers({...userAnswers, [exercise.id]: e.target.value})}
                />
              </div>
            ))}
          </div>

          <button className="submit-btn" onClick={handleSubmit}>
            🤖 提交并查看AI解析
          </button>
        </div>
      )}
    </div>
  );
};

export default GrammarPractice;
