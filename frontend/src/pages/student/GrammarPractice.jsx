import React, { useState, useEffect } from 'react';

const GrammarPractice = () => {
  const [grammarCategories, setGrammarCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [exercises, setExercises] = useState([]);
  const [userAnswers, setUserAnswers] = useState({});
  const [correctionResult, setCorrectionResult] = useState(null);
  const [loadingCategories, setLoadingCategories] = useState(false);
  const [loadingExercises, setLoadingExercises] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const getGrammarCategories = async () => {
      setLoadingCategories(true);
      try {
        const res = await fetch('/api/student/grammar/categories', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        if (!res.ok) throw new Error('网络请求失败');
        const result = await res.json();
        if (result.code !== 200) throw new Error(result.message || '获取语法分类失败');
        
        setGrammarCategories(result.data);
      } catch (err) {
        alert(err.message);
        console.error('获取语法分类错误：', err);
      } finally {
        setLoadingCategories(false);
      }
    };

    getGrammarCategories();
  }, []);

  useEffect(() => {
    if (!selectedCategory) return;

    const getExercisesByCategory = async () => {
      setLoadingExercises(true);
      setUserAnswers({});
      setCorrectionResult(null);
      setExercises([]);

      try {
        const res = await fetch(`/api/student/grammar/exercises?categoryId=${selectedCategory.id}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        if (!res.ok) throw new Error('网络请求失败');
        const result = await res.json();
        if (result.code !== 200) throw new Error(result.message || '获取练习题失败');
        
        setExercises(result.data);
      } catch (err) {
        alert(err.message);
        console.error('获取练习题错误：', err);
      } finally {
        setLoadingExercises(false);
      }
    };

    getExercisesByCategory();
  }, [selectedCategory]);

  const handleSelectCategory = (category) => {
    setSelectedCategory(category);
  };

  const handleSubmit = async () => {
    if (!selectedCategory) {
      alert('请先选择语法分类');
      return;
    }
    if (Object.keys(userAnswers).length !== exercises.length) {
      alert('请完成所有题目再提交');
      return;
    }

    setSubmitting(true);
    try {
      const answerList = Object.entries(userAnswers).map(([exerciseId, userAnswer]) => ({
        exerciseId: Number(exerciseId),
        userAnswer: userAnswer.trim()
      }));

      const res = await fetch('/api/student/grammar/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          categoryId: selectedCategory.id,
          answers: answerList
        })
      });
      if (!res.ok) throw new Error('网络请求失败');
      const result = await res.json();
      if (result.code !== 200) throw new Error(result.message || '提交答案失败');
      
      setCorrectionResult(result.data);
      alert('提交成功！已为你生成AI批改解析');
    } catch (err) {
      alert(err.message);
      console.error('提交答案错误：', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="grammar-practice-page">
      <div className="page-header">
        <h1>德语语法专题练习</h1>
        <p>选择语法点开始练习，AI将为你解析错题</p>
      </div>

      <div className="category-selector">
        {loadingCategories ? (
          <p>加载语法分类中...</p>
        ) : (
          grammarCategories.map(category => (
            <button
              key={category.id}
              className={selectedCategory?.id === category.id ? 'active' : ''}
              onClick={() => handleSelectCategory(category)}
            >
              {category.name}
              <span className="desc">{category.desc}</span>
            </button>
          ))
        )}
      </div>

      {selectedCategory && (
        <div className="exercise-section">
          <h2>当前练习：{selectedCategory.name}</h2>
          
          {loadingExercises ? (
            <p>加载练习题中...</p>
          ) : (
            <>
              <div className="exercise-list">
                {exercises.map(exercise => (
                  <div key={exercise.id} className="exercise-item">
                    <p className="question">{exercise.question}</p>
                    <input
                      type="text"
                      placeholder="请输入答案"
                      value={userAnswers[exercise.id] || ''}
                      onChange={(e) => setUserAnswers({...userAnswers, [exercise.id]: e.target.value})}
                      disabled={submitting || correctionResult}
                    />
                    {correctionResult && (
                      <div className="exercise-analysis">
                        {correctionResult.detailList.find(item => item.exerciseId === exercise.id)?.isCorrect ? (
                          <p style={{color: 'green'}}>✅ 回答正确</p>
                        ) : (
                          <>
                            <p style={{color: 'red'}}>❌ 回答错误</p>
                            <p>正确答案：{correctionResult.detailList.find(item => item.exerciseId === exercise.id)?.correctAnswer}</p>
                          </>
                        )}
                        <p>解析：{correctionResult.detailList.find(item => item.exerciseId === exercise.id)?.analysis}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {!correctionResult && (
                <button 
                  className="submit-btn" 
                  onClick={handleSubmit}
                  disabled={submitting || loadingExercises}
                >
                  {submitting ? '提交中...' : '🤖 提交并查看AI解析'}
                </button>
              )}

              {correctionResult && (
                <div className="result-overview">
                  <h3>批改结果</h3>
                  <p>总题数：{correctionResult.totalCount}</p>
                  <p>正确题数：{correctionResult.correctCount}</p>
                  <p>错误题数：{correctionResult.wrongCount}</p>
                  <p>正确率：{((correctionResult.correctCount / correctionResult.totalCount) * 100).toFixed(1)}%</p>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default GrammarPractice;