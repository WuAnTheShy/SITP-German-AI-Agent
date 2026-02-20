import React, { useState, useEffect } from 'react';

const ListeningSpeaking = () => {
  // 听力材料列表
  const [listeningMaterials, setListeningMaterials] = useState([]);
  // 当前选中的听力材料
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  // 选中材料的详情（含音频地址、原文等）
  const [materialDetail, setMaterialDetail] = useState(null);
  // 口语练习状态
  const [recording, setRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  // AI口语评分结果
  const [evaluationResult, setEvaluationResult] = useState(null);
  // 加载状态
  const [loadingMaterials, setLoadingMaterials] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [submittingEval, setSubmittingEval] = useState(false);

  // 页面加载时：获取听力材料列表（接口1）
  useEffect(() => {
    const getListeningMaterials = async () => {
      setLoadingMaterials(true);
      try {
        const res = await fetch('/api/student/listening/materials', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        if (!res.ok) throw new Error('网络请求失败');
        const result = await res.json();
        if (result.code !== 200) throw new Error(result.message || '获取听力材料失败');
        
        setListeningMaterials(result.data);
      } catch (err) {
        alert(err.message);
        console.error('获取听力材料错误：', err);
      } finally {
        setLoadingMaterials(false);
      }
    };

    getListeningMaterials();
  }, []);

  // 选中材料变化时：获取材料详情（含音频地址、原文，接口2）
  useEffect(() => {
    if (!selectedMaterial) return;

    const getMaterialDetail = async () => {
      setLoadingDetail(true);
      // 切换材料时清空之前的录音、评分结果
      setAudioUrl(null);
      setRecording(false);
      setEvaluationResult(null);
      setMaterialDetail(null);

      try {
        const res = await fetch(`/api/student/listening/material/detail?materialId=${selectedMaterial.id}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        if (!res.ok) throw new Error('网络请求失败');
        const result = await res.json();
        if (result.code !== 200) throw new Error(result.message || '获取材料详情失败');
        
        setMaterialDetail(result.data);
      } catch (err) {
        alert(err.message);
        console.error('获取材料详情错误：', err);
      } finally {
        setLoadingDetail(false);
      }
    };

    getMaterialDetail();
  }, [selectedMaterial]);

  // 选择听力材料
  const handleSelectMaterial = (material) => {
    setSelectedMaterial(material);
  };

  // 开始/结束录音
  const toggleRecording = () => {
    if (recording) {
      setRecording(false);
      // 模拟录音结束生成音频链接（后续可对接真实录音插件）
      setAudioUrl("https://example.com/recording.mp3");
    } else {
      setRecording(true);
      setAudioUrl(null);
      setEvaluationResult(null);
    }
  };

  // AI口语评分（接口3）
  const handleAIEvaluation = async () => {
    if (!audioUrl) {
      alert('请先完成录音再进行评分');
      return;
    }
    if (!selectedMaterial) {
      alert('请先选择听力材料');
      return;
    }

    setSubmittingEval(true);
    try {
      const res = await fetch('/api/student/speaking/evaluate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          materialId: selectedMaterial.id,
          audioUrl: audioUrl
        })
      });
      if (!res.ok) throw new Error('网络请求失败');
      const result = await res.json();
      if (result.code !== 200) throw new Error(result.message || '口语评分失败');
      
      setEvaluationResult(result.data);
      alert('AI评分完成！已为你生成发音解析');
    } catch (err) {
      alert(err.message);
      console.error('口语评分错误：', err);
    } finally {
      setSubmittingEval(false);
    }
  };

  return (
    <div className="listening-speaking-page">
      <div className="page-header">
        <h1>德语听说训练</h1>
        <p>听力磨耳朵 + 口语AI纠音，提升德语实战能力</p >
      </div>

      {/* 听力材料选择区 */}
      <div className="material-selector">
        {loadingMaterials ? (
          <p>加载听力材料中...</p >
        ) : (
          listeningMaterials.map(material => (
            <div
              key={material.id}
              className={`material-card ${selectedMaterial?.id === material.id ? 'active' : ''}`}
              onClick={() => handleSelectMaterial(material)}
            >
              <h3>{material.title}</h3>
              <div className="meta">
                <span>难度：{material.level}</span>
                <span>时长：{material.duration}</span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* 听力播放区 */}
      {selectedMaterial && (
        <div className="practice-section">
          <h2>当前练习：{selectedMaterial.title}</h2>
          
          {loadingDetail ? (
            <p>加载材料详情中...</p >
          ) : (
            materialDetail && (
              <>
                <div className="listening-player">
                  <audio src={materialDetail.audioUrl} controls />
                  <div className="script-box">
                    <h4>听力原文：</h4>
                    <p>{materialDetail.script}</p >
                  </div>
                </div>

                {/* 口语模仿区 */}
                <div className="speaking-area">
                  <h3>🎤 模仿口语练习</h3>
                  <p>听完后，点击下方按钮开始录音，模仿刚才的内容</p >
                  <button
                    className={`record-btn ${recording ? 'recording' : ''}`}
                    onClick={toggleRecording}
                    disabled={submittingEval}
                  >
                    {recording ? '⏹️ 结束录音' : '🎙️ 开始录音'}
                  </button>

                  {audioUrl && (
                    <div className="audio-preview">
                      <h4>你的录音：</h4>
                      <audio src={audioUrl} controls />
                      <button 
                        className="ai-eval-btn" 
                        onClick={handleAIEvaluation}
                        disabled={submittingEval}
                      >
                        {submittingEval ? '评分中...' : '🤖 AI口语评分'}
                      </button>
                    </div>
                  )}

                  {/* AI评分结果展示 */}
                  {evaluationResult && (
                    <div className="evaluation-result">
                      <h3>📊 AI评分结果</h3>
                      <div className="score-overview">
                        <div className="score-item">
                          <span>综合得分</span>
                          <strong>{evaluationResult.totalScore}分</strong>
                        </div>
                        <div className="score-item">
                          <span>发音准确度</span>
                          <strong>{evaluationResult.pronunciationScore}分</strong>
                        </div>
                        <div className="score-item">
                          <span>流利度</span>
                          <strong>{evaluationResult.fluencyScore}分</strong>
                        </div>
                        <div className="score-item">
                          <span>语调匹配度</span>
                          <strong>{evaluationResult.intonationScore}分</strong>
                        </div>
                      </div>
                      <div className="analysis-box">
                        <h4>🔍 详细解析</h4>
                        <p>{evaluationResult.analysis}</p >
                        <h4>💡 改进建议</h4>
                        <p>{evaluationResult.suggestion}</p >
                      </div>
                    </div>
                  )}
                </div>
              </>
            )
          )}
        </div>
      )}
    </div>
  );
};

export default ListeningSpeaking;