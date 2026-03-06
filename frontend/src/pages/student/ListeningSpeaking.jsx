import React, { useState, useEffect } from 'react';
import StudentLayout from '../../components/StudentLayout';
import request from '../../api/request';
import { API_LISTENING_MATERIALS, API_LISTENING_DETAIL, API_SPEAKING_EVALUATE } from '../../api/config';

const ListeningSpeaking = () => {
  const [listeningMaterials, setListeningMaterials] = useState([]);
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [materialDetail, setMaterialDetail] = useState(null);
  const [recording, setRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [evaluationResult, setEvaluationResult] = useState(null);
  const [loadingMaterials, setLoadingMaterials] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [submittingEval, setSubmittingEval] = useState(false);

  useEffect(() => {
    const getMaterials = async () => {
      setLoadingMaterials(true);
      try {
        const response = await request.get(API_LISTENING_MATERIALS);
        const result = response.data;
        if (result.code !== 200) throw new Error(result.message || '获取听力材料失败');
        setListeningMaterials(result.data);
      } catch (err) { alert(err.message); }
      finally { setLoadingMaterials(false); }
    };
    getMaterials();
  }, []);

  useEffect(() => {
    if (!selectedMaterial) return;
    const getDetail = async () => {
      setLoadingDetail(true); setAudioUrl(null); setRecording(false); setEvaluationResult(null); setMaterialDetail(null);
      try {
        const response = await request.get(API_LISTENING_DETAIL, { params: { materialId: selectedMaterial.id } });
        const result = response.data;
        if (result.code !== 200) throw new Error(result.message || '获取材料详情失败');
        setMaterialDetail(result.data);
      } catch (err) { alert(err.message); }
      finally { setLoadingDetail(false); }
    };
    getDetail();
  }, [selectedMaterial]);

  const toggleRecording = () => {
    if (recording) { setRecording(false); setAudioUrl("https://example.com/recording.mp3"); }
    else { setRecording(true); setAudioUrl(null); setEvaluationResult(null); }
  };

  const handleAIEvaluation = async () => {
    if (!audioUrl) { alert('请先完成录音再进行评分'); return; }
    if (!selectedMaterial) { alert('请先选择听力材料'); return; }
    setSubmittingEval(true);
    try {
      const response = await request.post(API_SPEAKING_EVALUATE, { materialId: selectedMaterial.id, audioUrl });
      const result = response.data;
      if (result.code !== 200) throw new Error(result.message || '口语评分失败');
      setEvaluationResult(result.data);
    } catch (err) { alert(err.message); }
    finally { setSubmittingEval(false); }
  };

  return (
    <StudentLayout>
      <div className="flex-1 overflow-y-auto p-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-200 mb-2">🎧 德语听说训练</h1>
          <p className="text-gray-500 dark:text-gray-400">听力磨耳朵 + 口语AI纠音，提升德语实战能力</p>
        </div>

        {/* 材料选择 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {loadingMaterials ? (
            <p className="text-gray-400 dark:text-gray-500 col-span-full text-center py-8">加载听力材料中...</p>
          ) : listeningMaterials.map(material => (
            <div key={material.id} onClick={() => setSelectedMaterial(material)}
              className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${selectedMaterial?.id === material.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30' : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-blue-300 hover:shadow-sm dark:shadow-gray-900/50'
                }`}>
              <h3 className="font-bold text-gray-800 dark:text-gray-200 mb-2">{material.title}</h3>
              <div className="flex gap-3 text-xs text-gray-500 dark:text-gray-400">
                <span>难度：{material.level}</span>
                <span>时长：{material.duration}</span>
              </div>
            </div>
          ))}
        </div>

        {/* 练习区 */}
        {selectedMaterial && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm dark:shadow-gray-900/50 border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-bold text-gray-700 dark:text-gray-300 mb-4">当前练习：{selectedMaterial.title}</h2>
            {loadingDetail ? (
              <p className="text-gray-400 dark:text-gray-500 py-8 text-center">加载材料详情中...</p>
            ) : materialDetail && (
              <>
                {/* 听力播放 */}
                <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <audio src={materialDetail.audioUrl} controls className="w-full mb-3" />
                  <div>
                    <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-1">听力原文：</h4>
                    <p className="text-gray-600 dark:text-gray-400 leading-relaxed">{materialDetail.script}</p>
                  </div>
                </div>

                {/* 口语模仿 */}
                <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
                  <h3 className="font-bold text-gray-800 dark:text-gray-200 mb-2">🎤 模仿口语练习</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">听完后，点击下方按钮开始录音，模仿刚才的内容</p>
                  <button onClick={toggleRecording} disabled={submittingEval}
                    className={`px-6 py-3 rounded-lg font-medium transition-colors ${recording ? 'bg-red-600 text-white hover:bg-red-700' : 'bg-blue-600 text-white hover:bg-blue-700'
                      } disabled:bg-gray-400`}>
                    {recording ? '⏹️ 结束录音' : '🎙️ 开始录音'}
                  </button>

                  {audioUrl && (
                    <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                      <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">你的录音：</h4>
                      <audio src={audioUrl} controls className="w-full mb-3" />
                      <button onClick={handleAIEvaluation} disabled={submittingEval}
                        className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 transition-colors font-medium">
                        {submittingEval ? '评分中...' : '🤖 AI口语评分'}
                      </button>
                    </div>
                  )}

                  {evaluationResult && (
                    <div className="mt-6 p-6 bg-blue-50 dark:bg-blue-900/30 rounded-xl border border-blue-200">
                      <h3 className="font-bold text-blue-800 mb-4">📊 AI评分结果</h3>
                      <div className="grid grid-cols-4 gap-4 mb-4">
                        {[
                          { label: '综合得分', score: evaluationResult.totalScore },
                          { label: '发音准确度', score: evaluationResult.pronunciationScore },
                          { label: '流利度', score: evaluationResult.fluencyScore },
                          { label: '语调匹配度', score: evaluationResult.intonationScore }
                        ].map((item, i) => (
                          <div key={i} className="text-center p-3 bg-white dark:bg-gray-800 rounded-lg">
                            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{item.score}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{item.label}</p>
                          </div>
                        ))}
                      </div>
                      <div className="space-y-3">
                        <div><h4 className="font-semibold text-gray-700 dark:text-gray-300">🔍 详细解析</h4><p className="text-gray-600 dark:text-gray-400 mt-1">{evaluationResult.analysis}</p></div>
                        <div><h4 className="font-semibold text-gray-700 dark:text-gray-300">💡 改进建议</h4><p className="text-gray-600 dark:text-gray-400 mt-1">{evaluationResult.suggestion}</p></div>
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </StudentLayout>
  );
};

export default ListeningSpeaking;
