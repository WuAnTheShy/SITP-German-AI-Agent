import React, { useState, useEffect } from 'react';
import StudentLayout from '../../components/StudentLayout';
import request from '../../api/request';
import {
  API_ERROR_LIST, API_ERROR_START_REVIEW,
  API_ERROR_MARK_MASTERED, API_ERROR_DELETE
} from '../../api/config';

const ErrorBookReview = () => {
  const [errorList, setErrorList] = useState([]);
  const [reviewMode, setReviewMode] = useState('browse');
  const [loading, setLoading] = useState({ page: false, review: false, operate: false });

  useEffect(() => { getErrorList(); }, []);

  const getErrorList = async () => {
    setLoading(prev => ({ ...prev, page: true }));
    try {
      const response = await request.get(API_ERROR_LIST);
      const data = response.data;
      if (data.code === 200) setErrorList(data.data);
      else throw new Error(data.message || '获取错题列表失败');
    } catch (error) { console.error('获取错题列表失败：', error); alert(`❌ ${error.message}`); }
    finally { setLoading(prev => ({ ...prev, page: false })); }
  };

  const handleStartReview = async () => {
    if (errorList.length === 0) { alert("暂无错题，无法开始复习！"); return; }
    setLoading(prev => ({ ...prev, review: true }));
    try {
      const response = await request.post(API_ERROR_START_REVIEW, { categoryId: null, categoryName: '所有错题' });
      const data = response.data;
      if (data.code === 200) { setReviewMode('review'); alert(data.data.reviewTip || '已开启所有错题的针对性复习！'); }
      else throw new Error(data.message || '开启复习失败');
    } catch (error) { alert(`❌ ${error.message}`); }
    finally { setLoading(prev => ({ ...prev, review: false })); }
  };

  const handleRemoveError = async (id, isMastered = false) => {
    setLoading(prev => ({ ...prev, operate: true }));
    try {
      let response;
      if (isMastered) {
        response = await request.post(API_ERROR_MARK_MASTERED, { errorId: id, categoryId: null });
      } else {
        response = await request.delete(`${API_ERROR_DELETE}/${id}`);
      }
      const data = response.data;
      if (data.code === 200) {
        setErrorList(prev => prev.filter(item => item.id !== id));
        if (isMastered) alert("已标记为掌握，错题已移除！");
      } else throw new Error(data.message || '操作失败');
    } catch (error) { alert(`❌ ${error.message}`); }
    finally { setLoading(prev => ({ ...prev, operate: false })); }
  };

  return (
    <StudentLayout>
      <div className="student-page">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-200 mb-2">📝 德语错题本与复习</h1>
          <p className="text-gray-500 dark:text-gray-400">收集所有错题，AI针对性生成复习计划，精准补漏</p>
        </div>

        {/* 复习操作 */}
        <div className="student-card flex items-center gap-4 mb-6 p-4">
          <button onClick={handleStartReview}
            disabled={reviewMode === 'review' || loading.review || loading.operate}
            className="student-action-primary px-6 py-3 rounded-lg disabled:bg-gray-400 disabled:cursor-not-allowed font-medium">
            {loading.review ? '正在开启复习...' : '🤖 开始AI针对性复习'}
          </button>
          <span className="text-sm text-gray-500 dark:text-gray-400">当前模式：
            <span className={`font-medium ${reviewMode === 'review' ? 'text-green-600' : 'text-gray-700 dark:text-gray-300'}`}>
              {reviewMode === 'browse' ? '错题浏览' : '专项复习'}
            </span>
          </span>
        </div>

        {/* 错题列表 */}
        {loading.page ? (
          <p className="text-center text-gray-400 dark:text-gray-500 py-8">正在加载错题列表...</p>
        ) : errorList.length === 0 ? (
          <div className="text-center py-12 text-gray-400 dark:text-gray-500">暂无错题，继续保持！🎉</div>
        ) : (
          <div className="space-y-4">
            {errorList.map(error => (
              <div key={error.id} className="student-card p-5">
                <div className="text-xs text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30 px-2 py-1 rounded w-fit mb-2">{error.source}</div>
                <p className="font-medium text-gray-800 dark:text-gray-200 mb-3">{error.question}</p>
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div className="p-3 bg-red-50 dark:bg-red-900/30 rounded-lg border border-red-100 dark:border-red-900/40">
                    <span className="text-xs text-red-500 block mb-1">你的答案</span>
                    <span className="text-red-700 dark:text-red-300">{error.userAnswer}</span>
                  </div>
                  <div className="p-3 bg-green-50 dark:bg-green-900/30 rounded-lg border border-green-100 dark:border-green-900/40">
                    <span className="text-xs text-green-500 block mb-1">正确答案</span>
                    <span className="text-green-700 dark:text-green-300">{error.correctAnswer}</span>
                  </div>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3"><span className="font-medium">解析：</span>{error.analysis}</p>
                <div className="flex gap-3">
                  <button onClick={() => handleRemoveError(error.id, true)} disabled={loading.operate}
                    className="px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 disabled:opacity-50 transition-colors text-sm">
                    {loading.operate ? '操作中...' : '✅ 标记已掌握'}
                  </button>
                  <button onClick={() => { if (window.confirm("确定要删除这条错题吗？")) handleRemoveError(error.id, false); }}
                    disabled={loading.operate}
                    className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 disabled:opacity-50 transition-colors text-sm">
                    删除错题
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </StudentLayout>
  );
};

export default ErrorBookReview;
