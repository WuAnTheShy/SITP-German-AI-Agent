import React, { useState } from 'react';
import StudentLayout from '../../components/StudentLayout';

const WritingAssistant = () => {
  const [userText, setUserText] = useState('');
  const [correctionResult, setCorrectionResult] = useState(null);
  const [sampleEssay, setSampleEssay] = useState('');
  const [isChecking, setIsChecking] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleCheckGrammar = async () => {
    if (!userText.trim()) { alert("请先输入德语文本哦！"); return; }
    setIsChecking(true);
    setCorrectionResult(null);
    try {
      const response = await fetch('/api/student/writing/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userText: userText.trim() })
      });
      const res = await response.json();
      if (res.code === 200) { setCorrectionResult(res.data); }
      else { alert(res.message || "语法检查失败，请稍后重试"); }
    } catch (error) {
      console.error("语法检查接口请求异常：", error);
      alert("接口请求失败，请检查网络或联系后端同学");
    } finally { setIsChecking(false); }
  };

  const handleGenerateSample = async () => {
    if (!userText.trim()) { alert("请先输入主题或开头文本哦！"); return; }
    setIsGenerating(true);
    setSampleEssay('');
    try {
      const response = await fetch('/api/student/writing/generate-sample', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userText: userText.trim() })
      });
      const res = await response.json();
      if (res.code === 200) { setSampleEssay(res.data.sampleEssay); }
      else { alert(res.message || "范文生成失败，请稍后重试"); }
    } catch (error) {
      console.error("范文生成接口请求异常：", error);
      alert("接口请求失败，请检查网络或联系后端同学");
    } finally { setIsGenerating(false); }
  };

  return (
    <StudentLayout>
      <div className="flex-1 overflow-y-auto p-8">
        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-800 mb-2">✍️ AI德语写作辅助</h1>
          <p className="text-gray-500">实时语法检查、智能润色、范文生成，轻松搞定德语写作</p>
        </div>

        {/* 输入区 */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <textarea
            placeholder="请输入你的德语作文、句子或主题..."
            value={userText}
            onChange={(e) => setUserText(e.target.value)}
            rows={8}
            disabled={isChecking || isGenerating}
            className="w-full p-4 border border-gray-200 rounded-lg resize-y focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 text-gray-800 placeholder-gray-400"
          />
          <div className="flex gap-3 mt-4">
            <button onClick={handleCheckGrammar} disabled={isChecking || isGenerating}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium">
              {isChecking ? "🔄 检查中..." : "🤖 检查语法并润色"}
            </button>
            <button onClick={handleGenerateSample} disabled={isChecking || isGenerating}
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium">
              {isGenerating ? "🔄 生成中..." : "📝 AI生成范文"}
            </button>
          </div>
        </div>

        {/* AI批改结果 */}
        {correctionResult && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
            <h3 className="text-lg font-bold text-green-700 mb-4">✅ AI批改结果</h3>
            <div className="mb-4">
              <h4 className="font-semibold text-gray-700 mb-2">发现的问题：</h4>
              <div className="space-y-2">
                {correctionResult.errors.map((err, index) => (
                  <div key={index} className="flex items-start gap-3 p-3 bg-red-50 rounded-lg border border-red-100">
                    <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded font-mono shrink-0">{err.position}</span>
                    <span className="text-red-600">{err.error}</span>
                    <span className="text-green-700 ml-auto shrink-0">→ {err.suggestion}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h4 className="font-semibold text-gray-700 mb-2">润色后的文本：</h4>
              <p className="p-4 bg-green-50 rounded-lg border border-green-100 text-gray-800 leading-relaxed">{correctionResult.polishedText}</p>
            </div>
          </div>
        )}

        {/* AI范文 */}
        {sampleEssay && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-bold text-blue-700 mb-4">📄 AI生成范文</h3>
            <p className="p-4 bg-blue-50 rounded-lg border border-blue-100 text-gray-800 leading-relaxed whitespace-pre-wrap">{sampleEssay}</p>
          </div>
        )}
      </div>
    </StudentLayout>
  );
};

export default WritingAssistant;
