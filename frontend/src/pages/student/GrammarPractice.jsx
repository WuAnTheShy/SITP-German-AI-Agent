import React, { useState, useEffect } from 'react';
import StudentLayout from '../../components/StudentLayout';
import request from '../../api/request';
import { API_GRAMMAR_CATEGORIES, API_GRAMMAR_EXERCISES, API_GRAMMAR_SUBMIT } from '../../api/config';

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
        const response = await request.get(API_GRAMMAR_CATEGORIES);
        const result = response.data;
        if (result.code !== 200) throw new Error(result.message || '获取语法分类失败');
        setGrammarCategories(result.data);
      } catch (err) { alert(err.message); console.error('获取语法分类错误：', err); }
      finally { setLoadingCategories(false); }
    };
    getGrammarCategories();
  }, []);

  useEffect(() => {
    if (!selectedCategory) return;
    const getExercises = async () => {
      setLoadingExercises(true); setUserAnswers({}); setCorrectionResult(null); setExercises([]);
      try {
        const response = await request.get(API_GRAMMAR_EXERCISES, { params: { categoryId: selectedCategory.id } });
        const result = response.data;
        if (result.code !== 200) throw new Error(result.message || '获取练习题失败');
        setExercises(result.data);
      } catch (err) { alert(err.message); console.error('获取练习题错误：', err); }
      finally { setLoadingExercises(false); }
    };
    getExercises();
  }, [selectedCategory]);

  const handleSubmit = async () => {
    if (!selectedCategory) { alert('请先选择语法分类'); return; }
    if (Object.keys(userAnswers).length !== exercises.length) { alert('请完成所有题目再提交'); return; }
    setSubmitting(true);
    try {
      const answerList = Object.entries(userAnswers).map(([exerciseId, userAnswer]) => ({
        exerciseId: Number(exerciseId), userAnswer: userAnswer.trim()
      }));
      const response = await request.post(API_GRAMMAR_SUBMIT, { categoryId: selectedCategory.id, answers: answerList });
      const result = response.data;
      if (result.code !== 200) throw new Error(result.message || '提交答案失败');
      setCorrectionResult(result.data);
    } catch (err) { alert(err.message); console.error('提交答案错误：', err); }
    finally { setSubmitting(false); }
  };

  return (
    <StudentLayout>
      <div className="flex-1 overflow-y-auto p-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-200 mb-2">📖 德语语法专题练习</h1>
          <p className="text-gray-500 dark:text-gray-400">选择语法点开始练习，AI将为你解析错题</p>
        </div>

        {/* 分类选择 */}
        <div className="flex gap-3 flex-wrap mb-6">
          {loadingCategories ? (
            <p className="text-gray-400 dark:text-gray-500">加载语法分类中...</p>
          ) : grammarCategories.map(cat => (
            <button key={cat.id} onClick={() => setSelectedCategory(cat)}
              className={`px-4 py-3 rounded-lg border-2 text-left transition-all ${selectedCategory?.id === cat.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-blue-300 text-gray-700 dark:text-gray-300'
                }`}>
              <strong className="block text-sm">{cat.name}</strong>
              <span className="text-xs text-gray-500 dark:text-gray-400">{cat.desc}</span>
            </button>
          ))}
        </div>

        {/* 练习区 */}
        {selectedCategory && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm dark:shadow-gray-900/50 border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-bold text-gray-700 dark:text-gray-300 mb-4">当前练习：{selectedCategory.name}</h2>
            {loadingExercises ? (
              <p className="text-gray-400 dark:text-gray-500 py-8 text-center">加载练习题中...</p>
            ) : (
              <>
                <div className="space-y-4 mb-6">
                  {exercises.map((exercise, idx) => {
                    const detail = correctionResult?.detailList?.find(item => item.exerciseId === exercise.id);
                    return (
                      <div key={exercise.id} className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-100 dark:border-gray-700">
                        <p className="font-medium text-gray-800 dark:text-gray-200 mb-2">{idx + 1}. {exercise.question}</p>
                        <input
                          type="text"
                          placeholder="请输入答案"
                          value={userAnswers[exercise.id] || ''}
                          onChange={(e) => setUserAnswers({ ...userAnswers, [exercise.id]: e.target.value })}
                          disabled={submitting || correctionResult}
                          className="dark:text-white w-full px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 dark:bg-gray-800"
                        />
                        {detail && (
                          <div className={`mt-2 p-3 rounded-lg ${detail.isCorrect ? 'bg-green-50 dark:bg-green-900/30 border border-green-200' : 'bg-red-50 dark:bg-red-900/30 border border-red-200'}`}>
                            <p className={`font-medium ${detail.isCorrect ? 'text-green-700' : 'text-red-700'}`}>
                              {detail.isCorrect ? '✅ 回答正确' : '❌ 回答错误'}
                            </p>
                            {!detail.isCorrect && <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">正确答案：{detail.correctAnswer}</p>}
                            <p className="text-sm text-gray-600 dark:text-white mt-1">解析：{detail.analysis}</p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {!correctionResult && (
                  <button onClick={handleSubmit} disabled={submitting || loadingExercises}
                    className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium">
                    {submitting ? '提交中...' : '🤖 提交并查看AI解析'}
                  </button>
                )}

                {correctionResult && (
                  <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/30 rounded-lg border border-blue-200">
                    <h3 className="font-bold text-blue-800 mb-2">📊 批改结果</h3>
                    <div className="grid grid-cols-4 gap-4 text-center">
                      <div><p className="text-2xl font-bold text-gray-800 dark:text-gray-200">{correctionResult.totalCount}</p><p className="text-xs text-gray-500 dark:text-gray-400">总题数</p></div>
                      <div><p className="text-2xl font-bold text-green-600">{correctionResult.correctCount}</p><p className="text-xs text-gray-500 dark:text-gray-400">正确</p></div>
                      <div><p className="text-2xl font-bold text-red-600">{correctionResult.wrongCount}</p><p className="text-xs text-gray-500 dark:text-gray-400">错误</p></div>
                      <div><p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{((correctionResult.correctCount / correctionResult.totalCount) * 100).toFixed(1)}%</p><p className="text-xs text-gray-500 dark:text-gray-400">正确率</p></div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </StudentLayout>
  );
};

export default GrammarPractice;
