import React, { useState, useEffect } from 'react';

// 接口基础配置：和上一个文件完全统一，后续只改这里就行
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
// 错题本相关接口地址（和上面的规范完全一致，绝对不能改）
const API_ERROR_CATEGORIES = `${API_BASE_URL}/api/student/error-book/categories`;
const API_ERROR_LIST = `${API_BASE_URL}/api/student/error-book/list`;
const API_START_REVIEW = `${API_BASE_URL}/api/student/error-book/start-review`;
const API_MARK_MASTERED = `${API_BASE_URL}/api/student/error-book/mark-mastered`;
const API_DELETE_ERROR = `${API_BASE_URL}/api/student/error-book/delete`;

const ErrorBookReview = () => {
  // 1. 状态管理
  const [errorCategories, setErrorCategories] = useState([]);
  const [selectedCate, setSelectedCate] = useState(null);
  const [errorList, setErrorList] = useState([]);
  const [reviewMode, setReviewMode] = useState('browse');
  const [loading, setLoading] = useState({
    page: false,
    list: false,
    review: false,
    operate: false
  });

  // 2. 页面加载时，自动获取错题分类列表
  useEffect(() => {
    getErrorCategories();
  }, []);

  // 3. 接口方法封装
  const getErrorCategories = async () => {
    setLoading(prev => ({ ...prev, page: true }));
    try {
      const response = await fetch(API_ERROR_CATEGORIES, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      const data = await response.json();

      if (data.code === 200) {
        setErrorCategories(data.data);
      } else {
        throw new Error(data.message || '获取错题分类失败');
      }
    } catch (error) {
      console.error('获取错题分类失败：', error);
      alert(`❌ ${error.message}`);
    } finally {
      setLoading(prev => ({ ...prev, page: false }));
    }
  };

  const getErrorList = async (categoryId) => {
    if (!categoryId) return;
    setLoading(prev => ({ ...prev, list: true }));
    try {
      const response = await fetch(`${API_ERROR_LIST}?categoryId=${categoryId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      const data = await response.json();

      if (data.code === 200) {
        setErrorList(data.data);
      } else {
        throw new Error(data.message || '获取错题列表失败');
      }
    } catch (error) {
      console.error('获取错题列表失败：', error);
      alert(`❌ ${error.message}`);
    } finally {
      setLoading(prev => ({ ...prev, list: false }));
    }
  };

  // 4. 页面交互方法
  const handleSelectCate = (cate) => {
    setSelectedCate(cate);
    setReviewMode('browse');
    getErrorList(cate.id);
  };

  const handleStartReview = async () => {
    if (!selectedCate) {
      alert("请先选择一个错题分类再开始复习！");
      return;
    }
    setLoading(prev => ({ ...prev, review: true }));
    try {
      const requestData = {
        categoryId: selectedCate.id,
        categoryName: selectedCate.name
      };

      const response = await fetch(API_START_REVIEW, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });
      const data = await response.json();

      if (data.code === 200) {
        setReviewMode('review');
        alert(data.data.reviewTip || `已开启【${selectedCate.name}】针对性复习，AI将生成同类练习题！`);
      } else {
        throw new Error(data.message || '开启复习失败');
      }
    } catch (error) {
      console.error('开启复习失败：', error);
      alert(`❌ ${error.message}`);
    } finally {
      setLoading(prev => ({ ...prev, review: false }));
    }
  };

  const handleRemoveError = async (id, isMastered = false) => {
    if (!selectedCate) return;
    setLoading(prev => ({ ...prev, operate: true }));
    try {
      let response;
      if (isMastered) {
        const requestData = {
          errorId: id,
          categoryId: selectedCate.id
        };
        response = await fetch(API_MARK_MASTERED, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(requestData)
        });
      } else {
        response = await fetch(`${API_DELETE_ERROR}/${id}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json'
          }
        });
      }

      const data = await response.json();
      if (data.code === 200) {
        setErrorList(prev => prev.filter(item => item.id !== id));
        setErrorCategories(prev => prev.map(cate => 
          cate.id === selectedCate.id ? { ...cate, count: Math.max(0, cate.count - 1) } : cate
        ));
        if (isMastered) {
          alert("已标记为掌握，错题已移除！");
        }
      } else {
        throw new Error(data.message || '操作失败');
      }
    } catch (error) {
      console.error('操作失败：', error);
      alert(`❌ ${error.message}`);
    } finally {
      setLoading(prev => ({ ...prev, operate: false }));
    }
  };

  const handleMastered = (id) => {
    handleRemoveError(id, true);
  };

  const handleDeleteError = (id) => {
    if (window.confirm("确定要删除这条错题吗？删除后无法恢复！")) {
      handleRemoveError(id, false);
    }
  };

  return (
    <div className="error-book-review-page">
      <div className="page-header">
        <h1>德语错题本与复习</h1>
        <p>收集所有错题，AI针对性生成复习计划，精准补漏</p>
      </div>

      <div className="error-cate-selector">
        {loading.page ? (
          <div className="loading-tip">正在加载错题分类...</div>
        ) : (
          errorCategories.map(cate => (
            <button
              key={cate.id}
              className={selectedCate?.id === cate.id ? 'active' : ''}
              onClick={() => handleSelectCate(cate)}
              disabled={loading.operate}
            >
              {cate.name}
              <span className="error-count">({cate.count}道)</span>
            </button>
          ))
        )}
      </div>

      {selectedCate && (
        <div className="error-action">
          <button 
            className="review-btn" 
            onClick={handleStartReview}
            disabled={reviewMode === 'review' || loading.review || loading.operate}
          >
            {loading.review ? '正在开启复习...' : '🤖 开始AI针对性复习'}
          </button>
          <p className="mode-tip">当前模式：{reviewMode === 'browse' ? '错题浏览' : '专项复习'}</p>
        </div>
      )}

      {selectedCate ? (
        <div className="error-list-section">
          <h2>【{selectedCate.name}】错题列表</h2>
          {loading.list ? (
            <div className="loading-tip">正在加载错题列表...</div>
          ) : errorList.length === 0 ? (
            <div className="no-error-tip">该分类暂无错题，继续保持！🎉</div>
          ) : (
            <div className="error-list">
              {errorList.map(error => (
                <div key={error.id} className="error-item">
                  <div className="error-source">{error.source}</div>
                  <p className="error-question">{error.question}</p>
                  <div className="answer-group">
                    <p><span className="label">你的答案：</span>{error.userAnswer}</p>
                    <p><span className="label correct">正确答案：</span>{error.correctAnswer}</p>
                  </div>
                  <p className="error-analysis"><span className="label">解析：</span>{error.analysis}</p>
                  <div className="error-btns">
                    <button 
                      onClick={() => handleMastered(error.id)}
                      disabled={loading.operate}
                    >
                      {loading.operate ? '操作中...' : '标记已掌握'}
                    </button>
                    <button 
                      onClick={() => handleDeleteError(error.id)} 
                      className="remove-btn"
                      disabled={loading.operate}
                    >
                      删除错题
                    </button>
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