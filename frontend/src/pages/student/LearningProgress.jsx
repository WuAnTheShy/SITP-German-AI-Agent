import React, { useState, useEffect } from 'react';
import StudentLayout from '../../components/StudentLayout';
import request from '../../api/request';
import { API_LEARNING_PROGRESS } from '../../api/config';

const LearningProgress = () => {
  const [learnStats, setLearnStats] = useState({
    totalTime: 0, weekTime: 0, finishRate: 0,
    modules: [], knowledge: [], weekReport: []
  });
  const [viewType, setViewType] = useState('overview');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const getProgress = async () => {
      setLoading(true);
      try {
        const response = await request.get(API_LEARNING_PROGRESS);
        const result = response.data;
        if (result.code !== 200) throw new Error(result.message || '获取学习数据失败');
        setLearnStats(result.data);
      } catch (err) { alert(err.message); }
      finally { setLoading(false); }
    };
    getProgress();
  }, []);

  const tabs = [
    { key: 'overview', label: '学习总览' },
    { key: 'module', label: '模块完成度' },
    { key: 'knowledge', label: '知识点掌握' },
    { key: 'week', label: '本周学习周报' },
  ];

  return (
    <StudentLayout>
      <div className="flex-1 overflow-y-auto p-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-200 mb-2">📊 我的学习进度统计</h1>
          <p className="text-gray-500 dark:text-gray-400 dark:text-gray-500">实时查看学习数据，AI分析学习情况，精准提升</p>
        </div>

        {/* Tab切换 */}
        <div className="flex gap-2 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg w-fit mb-6">
          {tabs.map(tab => (
            <button key={tab.key} onClick={() => setViewType(tab.key)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${viewType === tab.key ? 'bg-white dark:bg-gray-800 shadow text-blue-700 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400 dark:text-gray-500 hover:text-gray-800 dark:text-gray-200'}`}>
              {tab.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="text-center py-16 text-gray-400 dark:text-gray-500">正在加载你的学习数据...</div>
        ) : (
          <>
            {viewType === 'overview' && (
              <div className="space-y-6">
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm dark:shadow-gray-900/50 border border-gray-200 dark:border-gray-700 p-6 text-center">
                    <h3 className="text-sm text-gray-500 dark:text-gray-400 dark:text-gray-500 mb-2">总学习时长</h3>
                    <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">{learnStats.totalTime} <span className="text-base font-normal text-gray-500 dark:text-gray-400 dark:text-gray-500">小时</span></p>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm dark:shadow-gray-900/50 border border-gray-200 dark:border-gray-700 p-6 text-center">
                    <h3 className="text-sm text-gray-500 dark:text-gray-400 dark:text-gray-500 mb-2">本周学习时长</h3>
                    <p className="text-3xl font-bold text-green-600">{learnStats.weekTime} <span className="text-base font-normal text-gray-500 dark:text-gray-400 dark:text-gray-500">小时</span></p>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm dark:shadow-gray-900/50 border border-gray-200 dark:border-gray-700 p-6 text-center">
                    <h3 className="text-sm text-gray-500 dark:text-gray-400 dark:text-gray-500 mb-2">整体完成率</h3>
                    <p className="text-3xl font-bold text-purple-600">{learnStats.finishRate}%</p>
                    <div className="mt-2 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div className="h-full bg-purple-500 rounded-full transition-all" style={{ width: `${learnStats.finishRate}%` }}></div>
                    </div>
                  </div>
                </div>
                <div className="bg-blue-50 dark:bg-blue-900/30 rounded-xl p-6 border border-blue-200">
                  <h4 className="font-bold text-blue-800 mb-2">🤖 AI学习分析</h4>
                  <p className="text-gray-700 dark:text-gray-300">本周学习时长较上周提升20%，但语法和写作模块完成度偏低，建议后续重点练习！</p>
                </div>
              </div>
            )}

            {viewType === 'module' && (
              <div className="space-y-3">
                {learnStats.modules.length === 0 ? (
                  <p className="text-center text-gray-400 dark:text-gray-500 py-8">暂无模块学习数据</p>
                ) : learnStats.modules.map((item, index) => (
                  <div key={index} className="flex items-center gap-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
                    <div className="w-32 font-medium text-gray-700 dark:text-gray-300">{item.name}</div>
                    <div className="flex-1 h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all" style={{
                        width: `${item.rate}%`,
                        backgroundColor: item.rate >= 80 ? '#22c55e' : item.rate >= 60 ? '#eab308' : '#ef4444'
                      }}></div>
                    </div>
                    <div className="w-16 text-right font-bold text-gray-700 dark:text-gray-300">{item.rate}%</div>
                  </div>
                ))}
              </div>
            )}

            {viewType === 'knowledge' && (
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                {learnStats.knowledge.length === 0 ? (
                  <p className="text-center text-gray-400 dark:text-gray-500 py-8 col-span-full">暂无知识点学习数据</p>
                ) : learnStats.knowledge.map((item, index) => (
                  <div key={index} className={`p-4 rounded-xl border-2 ${item.level === '熟练' ? 'border-green-300 bg-green-50 dark:bg-green-900/30' :
                      item.level === '一般' ? 'border-yellow-300 bg-yellow-50' :
                        'border-red-300 bg-red-50 dark:bg-red-900/30'
                    }`}>
                    <div className="font-medium text-gray-800 dark:text-gray-200">{item.name}</div>
                    <div className={`text-sm font-bold mt-1 ${item.level === '熟练' ? 'text-green-700' :
                        item.level === '一般' ? 'text-yellow-700' : 'text-red-700'
                      }`}>{item.level}</div>
                  </div>
                ))}
              </div>
            )}

            {viewType === 'week' && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm dark:shadow-gray-900/50 border border-gray-200 dark:border-gray-700 overflow-hidden">
                <div className="p-4 border-b border-gray-100 dark:border-gray-700"><h3 className="font-bold text-gray-700 dark:text-gray-300">本周学习明细</h3></div>
                {learnStats.weekReport.length === 0 ? (
                  <p className="text-center text-gray-400 dark:text-gray-500 py-8">本周暂无学习记录，快去学习吧！</p>
                ) : (
                  <table className="w-full">
                    <thead className="bg-gray-50 dark:bg-gray-900">
                      <tr>
                        <th className="text-left px-6 py-3 text-sm font-medium text-gray-500 dark:text-gray-400 dark:text-gray-500">星期</th>
                        <th className="text-left px-6 py-3 text-sm font-medium text-gray-500 dark:text-gray-400 dark:text-gray-500">学习时长（小时）</th>
                        <th className="text-left px-6 py-3 text-sm font-medium text-gray-500 dark:text-gray-400 dark:text-gray-500">学习内容</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                      {learnStats.weekReport.map((item, index) => (
                        <tr key={index} className="hover:bg-gray-50 dark:bg-gray-900">
                          <td className="px-6 py-3 text-gray-700 dark:text-gray-300">{item.day}</td>
                          <td className="px-6 py-3 text-gray-700 dark:text-gray-300">{item.time}</td>
                          <td className="px-6 py-3 text-gray-700 dark:text-gray-300">{item.content}</td>
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
    </StudentLayout>
  );
};

export default LearningProgress;
