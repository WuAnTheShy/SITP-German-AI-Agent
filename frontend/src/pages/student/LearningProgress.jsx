import React, { useState, useEffect } from 'react';

const LearningProgress = () => {
  const [learnStats, setLearnStats] = useState({
    totalTime: 0,
    weekTime: 0,
    finishRate: 0,
    modules: [],
    knowledge: [],
    weekReport: []
  });
  const [viewType, setViewType] = useState('overview');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const getLearningProgress = async () => {
      setLoading(true);
      try {
        const res = await fetch('/api/student/learning/progress', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        if (!res.ok) throw new Error('网络请求失败');
        const result = await res.json();
        if (result.code !== 200) throw new Error(result.message || '获取学习数据失败');
        
        setLearnStats(result.data);
      } catch (err) {
        alert(err.message);
        console.error('获取学习进度错误：', err);
      } finally {
        setLoading(false);
      }
    };

    getLearningProgress();
  }, []);

  return (
    <div className="learning-progress-page">
      <div className="page-header">
        <h1>我的学习进度统计</h1>
        <p>实时查看学习数据，AI分析学习情况，精准提升</p>
      </div>

      <div className="view-switch">
        <button 
          className={viewType === 'overview' ? 'active' : ''}
          onClick={() => setViewType('overview')}
        >
          学习总览
        </button>
        <button 
          className={viewType === 'module' ? 'active' : ''}
          onClick={() => setViewType('module')}
        >
          模块完成度
        </button>
        <button 
          className={viewType === 'knowledge' ? 'active' : ''}
          onClick={() => setViewType('knowledge')}
        >
          知识点掌握
        </button>
        <button 
          className={viewType === 'week' ? 'active' : ''}
          onClick={() => setViewType('week')}
        >
          本周学习周报
        </button>
      </div>

      {loading ? (
        <div className="loading-box">
          <p>正在加载你的学习数据...</p>
        </div>
      ) : (
        <>
          {viewType === 'overview' && (
            <div className="overview-section">
              <div className="stats-card">
                <h3>总学习时长</h3>
                <p className="stats-num">{learnStats.totalTime} 小时</p>
              </div>
              <div className="stats-card">
                <h3>本周学习时长</h3>
                <p className="stats-num">{learnStats.weekTime} 小时</p>
              </div>
              <div className="stats-card">
                <h3>整体完成率</h3>
                <p className="stats-num">{learnStats.finishRate} %</p>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${learnStats.finishRate}%` }}></div>
                </div>
              </div>
              <div className="ai-analysis">
                <h4>🤖 AI学习分析</h4>
                <p>本周学习时长较上周提升20%，但语法和写作模块完成度偏低，建议后续重点练习！</p>
              </div>
            </div>
          )}

          {viewType === 'module' && (
            <div className="module-section">
              {learnStats.modules.length === 0 ? (
                <p className="empty-tip">暂无模块学习数据</p>
              ) : (
                learnStats.modules.map((item, index) => (
                  <div key={index} className="module-item">
                    <div className="module-name">{item.name}</div>
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ 
                          width: `${item.rate}%`, 
                          backgroundColor: item.rate >= 80 ? '#4CAF50' : item.rate >= 60 ? '#FFC107' : '#F44336' 
                        }}
                      ></div>
                    </div>
                    <div className="module-rate">{item.rate} %</div>
                  </div>
                ))
              )}
            </div>
          )}

          {viewType === 'knowledge' && (
            <div className="knowledge-section">
              {learnStats.knowledge.length === 0 ? (
                <p className="empty-tip">暂无知识点学习数据</p>
              ) : (
                learnStats.knowledge.map((item, index) => (
                  <div 
                    key={index} 
                    className={`knowledge-item ${item.level === '熟练' ? 'proficient' : item.level === '一般' ? 'average' : 'weak'}`}
                  >
                    <div className="know-name">{item.name}</div>
                    <div className="know-level">{item.level}</div>
                  </div>
                ))
              )}
            </div>
          )}

          {viewType === 'week' && (
            <div className="week-report-section">
              <h3>本周学习明细</h3>
              {learnStats.weekReport.length === 0 ? (
                <p className="no-report">本周暂无学习记录，快去学习吧！</p>
              ) : (
                <table className="week-table">
                  <thead>
                    <tr>
                      <th>星期</th>
                      <th>学习时长（小时）</th>
                      <th>学习内容</th>
                    </tr>
                  </thead>
                  <tbody>
                    {learnStats.weekReport.map((item, index) => (
                      <tr key={index}>
                        <td>{item.day}</td>
                        <td>{item.time}</td>
                        <td>{item.content}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default LearningProgress;