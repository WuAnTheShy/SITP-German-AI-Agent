import React, { useState } from 'react';

const LearningProgress = () => {
  // 模拟核心学习统计数据
  const [learnStats, setLearnStats] = useState({
    totalTime: 12.5, // 总学习时长（小时）
    weekTime: 3.2,   // 本周学习时长（小时）
    finishRate: 68,  // 整体学习完成率（%）
    modules: [       // 各模块完成度
      { name: "词汇学习", rate: 85 },
      { name: "语法练习", rate: 72 },
      { name: "听说训练", rate: 55 },
      { name: "写作辅助", rate: 48 },
      { name: "场景对话", rate: 60 }
    ],
    knowledge: [     // 知识点掌握度（按等级）
      { name: "A1基础词汇", level: "熟练" },
      { name: "现在时/过去时", level: "熟练" },
      { name: "介词搭配", level: "一般" },
      { name: "从句用法", level: "薄弱" },
      { name: "口语发音", level: "一般" }
    ],
    weekReport: [    // 本周学习周报数据
      { day: "周一", time: 0.8, content: "词汇闪卡练习" },
      { day: "周三", time: 1.0, content: "语法专题-完成时" },
      { day: "周五", time: 0.6, content: "听说训练-校园对话" },
      { day: "周日", time: 0.8, content: "AI写作批改练习" }
    ]
  });

  // 切换统计视图（总览/模块/知识点/周报）
  const [viewType, setViewType] = useState('overview');

  return (
    <div className="learning-progress-page">
      <div className="page-header">
        <h1>我的学习进度统计</h1>
        <p>实时查看学习数据，AI分析学习情况，精准提升</p >
      </div>

      {/* 视图切换按钮 */}
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

      {/* 学习总览视图 */}
      {viewType === 'overview' && (
        <div className="overview-section">
          <div className="stats-card">
            <h3>总学习时长</h3>
            <p className="stats-num">{learnStats.totalTime} 小时</p >
          </div>
          <div className="stats-card">
            <h3>本周学习时长</h3>
            <p className="stats-num">{learnStats.weekTime} 小时</p >
          </div>
          <div className="stats-card">
            <h3>整体完成率</h3>
            <p className="stats-num">{learnStats.finishRate} %</p >
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${learnStats.finishRate}%` }}></div>
            </div>
          </div>
          <div className="ai-analysis">
            <h4>🤖 AI学习分析</h4>
            <p>本周学习时长较上周提升20%，但语法和写作模块完成度偏低，建议后续重点练习！</p >
          </div>
        </div>
      )}

      {/* 模块完成度视图 */}
      {viewType === 'module' && (
        <div className="module-section">
          {learnStats.modules.map((item, index) => (
            <div key={index} className="module-item">
              <div className="module-name">{item.name}</div>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${item.rate}%`, backgroundColor: item.rate >= 80 ? '#4CAF50' : item.rate >= 60 ? '#FFC107' : '#F44336' }}></div>
              </div>
              <div className="module-rate">{item.rate} %</div>
            </div>
          ))}
        </div>
      )}

      {/* 知识点掌握视图 */}
      {viewType === 'knowledge' && (
        <div className="knowledge-section">
          {learnStats.knowledge.map((item, index) => (
            <div key={index} className={`knowledge-item ${item.level === '熟练' ? 'proficient' : item.level === '一般' ? 'average' : 'weak'}`}>
              <div className="know-name">{item.name}</div>
              <div className="know-level">{item.level}</div>
            </div>
          ))}
        </div>
      )}

      {/* 本周学习周报视图 */}
      {viewType === 'week' && (
        <div className="week-report-section">
          <h3>本周学习明细</h3>
          {learnStats.weekReport.length === 0 ? (
            <p className="no-report">本周暂无学习记录，快去学习吧！</p >
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
    </div>
  );
};

export default LearningProgress;
