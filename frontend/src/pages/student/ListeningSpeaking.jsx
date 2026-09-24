import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  AlertCircle,
  BarChart3,
  BookOpen,
  CheckCircle2,
  Clock3,
  Headphones,
  History,
  Languages,
  Loader2,
  Mic,
  Pause,
  Play,
  RotateCcw,
  Search,
  Sparkles,
  Square,
  Upload,
  Volume2,
  Waves,
} from "lucide-react";
import StudentLayout from "../../components/StudentLayout";
import request from "../../api/request";
import {
  API_LISTENING_DETAIL,
  API_LISTENING_MATERIALS,
  API_SPEAKING_EVALUATE_AUDIO,
  API_SPEAKING_HISTORY,
} from "../../api/config";

const LEVELS = ["全部", "A1", "A2", "B1", "B2", "C1", "C2"];
const MAX_RECORDING_SECONDS = 120;

const formatSeconds = (seconds) => {
  const safe = Math.max(0, Math.round(seconds || 0));
  return `${String(Math.floor(safe / 60)).padStart(2, "0")}:${String(safe % 60).padStart(2, "0")}`;
};

const formatDate = (value) => {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? ""
    : date.toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
};

const scoreTone = (score) => {
  if (score >= 85) return "text-emerald-600 dark:text-emerald-400";
  if (score >= 70) return "text-blue-600 dark:text-blue-400";
  if (score >= 60) return "text-amber-600 dark:text-amber-400";
  return "text-rose-600 dark:text-rose-400";
};

const ListeningSpeaking = () => {
  const [materials, setMaterials] = useState([]);
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [materialDetail, setMaterialDetail] = useState(null);
  const [level, setLevel] = useState("全部");
  const [search, setSearch] = useState("");
  const [showScript, setShowScript] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [audioFailed, setAudioFailed] = useState(false);
  const [ttsPlaying, setTtsPlaying] = useState(false);

  const [recording, setRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [recordingBlob, setRecordingBlob] = useState(null);
  const [recordingUrl, setRecordingUrl] = useState("");
  const [transcript, setTranscript] = useState("");
  const [liveTranscript, setLiveTranscript] = useState("");
  const [pauseCount, setPauseCount] = useState(0);
  const [intonationVariation, setIntonationVariation] = useState(0);
  const [evaluation, setEvaluation] = useState(null);
  const [history, setHistory] = useState([]);

  const [loadingMaterials, setLoadingMaterials] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });

  const audioRef = useRef(null);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const recordingElapsedRef = useRef(0);
  const timerRef = useRef(null);
  const meterTimerRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const volumeSamplesRef = useRef([]);
  const silenceSampleCountRef = useRef(0);
  const pauseCounterRef = useRef(0);
  const recognitionRef = useRef(null);
  const finalTranscriptRef = useRef("");

  const speechRecognitionSupported = Boolean(
    typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition),
  );
  const microphoneSupported = Boolean(
    typeof navigator !== "undefined" && navigator.mediaDevices?.getUserMedia && window.MediaRecorder,
  );

  useEffect(() => {
    const loadMaterials = async () => {
      setLoadingMaterials(true);
      try {
        const response = await request.get(API_LISTENING_MATERIALS);
        const result = response.data;
        if (result.code !== 200) throw new Error(result.message || "获取听力材料失败");
        const rows = Array.isArray(result.data) ? result.data : [];
        setMaterials(rows);
        if (rows.length) setSelectedMaterial(rows[0]);
      } catch (error) {
        setMessage({ type: "error", text: error.response?.data?.message || error.message || "获取听力材料失败" });
      } finally {
        setLoadingMaterials(false);
      }
    };

    const loadHistory = async () => {
      setLoadingHistory(true);
      try {
        const response = await request.get(API_SPEAKING_HISTORY, { params: { limit: 8 } });
        const result = response.data;
        if (result.code === 200) setHistory(Array.isArray(result.data) ? result.data : []);
      } catch {
        setHistory([]);
      } finally {
        setLoadingHistory(false);
      }
    };

    loadMaterials();
    loadHistory();
  }, []);

  useEffect(() => {
    if (!selectedMaterial) return undefined;
    let cancelled = false;
    const loadDetail = async () => {
      setLoadingDetail(true);
      setMaterialDetail(null);
      setShowScript(false);
      setAudioFailed(false);
      setMessage({ type: "", text: "" });
      try {
        const response = await request.get(API_LISTENING_DETAIL, {
          params: { materialId: selectedMaterial.id },
        });
        const result = response.data;
        if (result.code !== 200) throw new Error(result.message || "获取材料详情失败");
        if (!cancelled) setMaterialDetail(result.data);
      } catch (error) {
        if (!cancelled) setMessage({ type: "error", text: error.message || "获取材料详情失败" });
      } finally {
        if (!cancelled) setLoadingDetail(false);
      }
    };
    loadDetail();
    return () => { cancelled = true; };
  }, [selectedMaterial]);

  useEffect(() => {
    if (audioRef.current) audioRef.current.playbackRate = playbackRate;
  }, [playbackRate]);

  useEffect(() => () => {
    window.speechSynthesis?.cancel();
    if (timerRef.current) window.clearInterval(timerRef.current);
    if (meterTimerRef.current) window.clearInterval(meterTimerRef.current);
    recognitionRef.current?.abort?.();
    mediaRecorderRef.current?.state === "recording" && mediaRecorderRef.current.stop();
    streamRef.current?.getTracks().forEach((track) => track.stop());
    audioContextRef.current?.close?.();
  }, []);

  useEffect(() => () => {
    if (recordingUrl) URL.revokeObjectURL(recordingUrl);
  }, [recordingUrl]);

  const filteredMaterials = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    return materials.filter((item) => {
      const matchesLevel = level === "全部" || item.level === level;
      const matchesSearch = !keyword || item.title.toLowerCase().includes(keyword);
      return matchesLevel && matchesSearch;
    });
  }, [level, materials, search]);

  const resetAttempt = () => {
    setRecordingBlob(null);
    setRecordingUrl("");
    setRecordingSeconds(0);
    setTranscript("");
    setLiveTranscript("");
    setPauseCount(0);
    setIntonationVariation(0);
    setEvaluation(null);
    finalTranscriptRef.current = "";
  };

  const selectMaterial = (material) => {
    if (recording) return;
    window.speechSynthesis?.cancel();
    setTtsPlaying(false);
    resetAttempt();
    setSelectedMaterial(material);
  };

  const speakScript = () => {
    const script = materialDetail?.script?.trim();
    if (!script || !window.speechSynthesis) {
      setMessage({ type: "error", text: "当前浏览器不支持语音朗读，请更换新版 Edge 或 Chrome。" });
      return;
    }
    if (ttsPlaying) {
      window.speechSynthesis.cancel();
      setTtsPlaying(false);
      return;
    }
    const utterance = new SpeechSynthesisUtterance(script);
    utterance.lang = "de-DE";
    utterance.rate = playbackRate;
    const germanVoice = window.speechSynthesis.getVoices().find((voice) => voice.lang?.toLowerCase().startsWith("de"));
    if (germanVoice) utterance.voice = germanVoice;
    utterance.onend = () => setTtsPlaying(false);
    utterance.onerror = () => {
      setTtsPlaying(false);
      setMessage({ type: "error", text: "德语朗读启动失败，请检查系统语音包。" });
    };
    setTtsPlaying(true);
    window.speechSynthesis.speak(utterance);
  };

  const stopRecognitionAndMeter = () => {
    if (timerRef.current) window.clearInterval(timerRef.current);
    if (meterTimerRef.current) window.clearInterval(meterTimerRef.current);
    timerRef.current = null;
    meterTimerRef.current = null;
    recognitionRef.current?.stop?.();
    recognitionRef.current = null;

    const samples = volumeSamplesRef.current;
    if (samples.length) {
      const mean = samples.reduce((sum, value) => sum + value, 0) / samples.length;
      const variance = samples.reduce((sum, value) => sum + ((value - mean) ** 2), 0) / samples.length;
      setIntonationVariation(mean > 0 ? Math.sqrt(variance) / mean : 0);
    }
    setPauseCount(pauseCounterRef.current);
    audioContextRef.current?.close?.();
    audioContextRef.current = null;
    analyserRef.current = null;
  };

  const stopRecording = () => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state !== "recording") return;
    setRecording(false);
    const elapsed = Math.min(MAX_RECORDING_SECONDS, Math.max(1, recordingElapsedRef.current));
    setRecordingSeconds(elapsed);
    stopRecognitionAndMeter();
    recorder.stop();
  };

  const startRecording = async () => {
    if (!selectedMaterial || !materialDetail) {
      setMessage({ type: "error", text: "请先选择并加载一篇听力材料。" });
      return;
    }
    if (!microphoneSupported) {
      setMessage({
        type: "error",
        text: "当前页面无法访问麦克风。服务器部署时需启用 HTTPS；也可以上传录音并手动填写转写。",
      });
      return;
    }
    try {
      resetAttempt();
      setMessage({ type: "", text: "" });
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      streamRef.current = stream;
      const preferredTypes = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"];
      const mimeType = preferredTypes.find((type) => MediaRecorder.isTypeSupported(type));
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data?.size) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        setRecordingBlob(blob);
        setRecordingUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      };

      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        const context = new AudioContextClass();
        const analyser = context.createAnalyser();
        analyser.fftSize = 1024;
        context.createMediaStreamSource(stream).connect(analyser);
        audioContextRef.current = context;
        analyserRef.current = analyser;
        volumeSamplesRef.current = [];
        pauseCounterRef.current = 0;
        silenceSampleCountRef.current = 0;
        const timeData = new Uint8Array(analyser.fftSize);
        meterTimerRef.current = window.setInterval(() => {
          analyser.getByteTimeDomainData(timeData);
          const rms = Math.sqrt(
            timeData.reduce((sum, value) => sum + (((value - 128) / 128) ** 2), 0) / timeData.length,
          );
          if (rms > 0.006) volumeSamplesRef.current.push(rms);
          if (rms < 0.018) {
            silenceSampleCountRef.current += 1;
          } else if (silenceSampleCountRef.current) {
            if (silenceSampleCountRef.current >= 7) pauseCounterRef.current += 1;
            silenceSampleCountRef.current = 0;
          }
        }, 100);
      }

      if (speechRecognitionSupported) {
        const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new Recognition();
        recognition.lang = "de-DE";
        recognition.continuous = true;
        recognition.interimResults = true;
        finalTranscriptRef.current = "";
        recognition.onresult = (event) => {
          let finalText = finalTranscriptRef.current;
          let interimText = "";
          for (let index = event.resultIndex; index < event.results.length; index += 1) {
            const text = event.results[index][0]?.transcript || "";
            if (event.results[index].isFinal) finalText = `${finalText} ${text}`.trim();
            else interimText += text;
          }
          finalTranscriptRef.current = finalText;
          setTranscript(finalText);
          setLiveTranscript(interimText);
        };
        recognition.onerror = () => setLiveTranscript("");
        recognitionRef.current = recognition;
        recognition.start();
      }

      recordingElapsedRef.current = 0;
      setRecording(true);
      recorder.start(250);
      timerRef.current = window.setInterval(() => {
        recordingElapsedRef.current += 0.25;
        const elapsed = recordingElapsedRef.current;
        setRecordingSeconds(elapsed);
        if (elapsed >= MAX_RECORDING_SECONDS) stopRecording();
      }, 250);
    } catch (error) {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      setRecording(false);
      setMessage({
        type: "error",
        text: error.name === "NotAllowedError"
          ? "麦克风权限被拒绝，请在浏览器地址栏中允许麦克风后重试。"
          : `无法开始录音：${error.message || "未知错误"}`,
      });
    }
  };

  const handleAudioUpload = (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (!file.type.startsWith("audio/")) {
      setMessage({ type: "error", text: "请选择音频文件。" });
      return;
    }
    if (file.size > 12 * 1024 * 1024) {
      setMessage({ type: "error", text: "录音文件不能超过 12 MB。" });
      return;
    }
    resetAttempt();
    setRecordingBlob(file);
    setRecordingUrl(URL.createObjectURL(file));
    setMessage({ type: "info", text: "录音已载入，请填写或校正德语转写文本后评分。" });
  };

  const submitEvaluation = async () => {
    if (!recordingBlob || !selectedMaterial) {
      setMessage({ type: "error", text: "请先录音或上传录音文件。" });
      return;
    }
    if (!transcript.trim()) {
      setMessage({ type: "error", text: "未识别到语音，请在转写框中手动输入你实际朗读的德语内容。" });
      return;
    }
    setSubmitting(true);
    setEvaluation(null);
    setMessage({ type: "", text: "" });
    try {
      const formData = new FormData();
      formData.append("materialId", String(selectedMaterial.id));
      formData.append("transcript", transcript.trim());
      formData.append("durationSeconds", String(Math.max(recordingSeconds, 1)));
      formData.append("pauseCount", String(pauseCount));
      formData.append("intonationVariation", String(intonationVariation));
      const extension = recordingBlob.type.includes("ogg") ? "ogg"
        : recordingBlob.type.includes("mp4") ? "m4a"
          : recordingBlob.type.includes("wav") ? "wav" : "webm";
      formData.append("audio", recordingBlob, `speaking-${Date.now()}.${extension}`);
      const response = await request.post(API_SPEAKING_EVALUATE_AUDIO, formData, { timeout: 90000 });
      const result = response.data;
      if (result.code !== 200) throw new Error(result.message || "口语评分失败");
      setEvaluation(result.data);
      setHistory((current) => [{
        id: result.data.evaluationId,
        materialTitle: selectedMaterial.title,
        level: selectedMaterial.level,
        totalScore: result.data.totalScore,
        pronunciationScore: result.data.pronunciationScore,
        fluencyScore: result.data.fluencyScore,
        intonationScore: result.data.intonationScore,
        analysis: result.data.analysis,
        suggestion: result.data.suggestion,
        evaluatedAt: result.data.evaluatedAt,
      }, ...current].slice(0, 8));
      setMessage({ type: "success", text: "评测完成，结果已保存到训练记录。" });
    } catch (error) {
      setMessage({
        type: "error",
        text: error.response?.data?.message || error.response?.data?.detail || error.message || "口语评分失败",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <StudentLayout>
      <div className="student-page overflow-y-auto">
        <div className="mx-auto w-full max-w-7xl pb-10">
          <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-sky-600 via-blue-600 to-indigo-700 p-6 text-white shadow-xl md:p-8">
            <div className="absolute -right-16 -top-20 h-64 w-64 rounded-full bg-white/10 blur-2xl" />
            <div className="relative flex flex-col justify-between gap-6 md:flex-row md:items-center">
              <div>
                <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-sm backdrop-blur"><Sparkles size={15} /> Hören · Sprechen</div>
                <h1 className="text-3xl font-black tracking-tight md:text-4xl">德语听说训练</h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-blue-100 md:text-base">先精听、再跟读。系统会结合德语转写准确度、语速、停顿和声音变化生成可解释评分。</p>
              </div>
              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="rounded-2xl bg-white/[0.12] px-5 py-3 backdrop-blur"><p className="text-2xl font-black">{materials.length}</p><p className="text-xs text-blue-100">训练材料</p></div>
                <div className="rounded-2xl bg-white/[0.12] px-5 py-3 backdrop-blur"><p className="text-2xl font-black">{history.length}</p><p className="text-xs text-blue-100">近期评测</p></div>
              </div>
            </div>
          </section>

          {message.text && (
            <div className={`mt-5 flex items-start gap-3 rounded-2xl border px-4 py-3 text-sm ${message.type === "error" ? "border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300" : message.type === "success" ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300" : "border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-900 dark:bg-blue-950/40 dark:text-blue-300"}`}>
              {message.type === "success" ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}<span>{message.text}</span>
            </div>
          )}

          <div className="mt-6 grid gap-6 xl:grid-cols-[340px_minmax(0,1fr)]">
            <aside className="student-card h-fit p-5 xl:sticky xl:top-4">
              <div className="flex items-center gap-2"><Headphones className="text-blue-600" size={21} /><h2 className="font-bold text-slate-800 dark:text-slate-100">选择听力材料</h2></div>
              <div className="relative mt-4">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={17} />
                <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索材料" className="student-input w-full rounded-xl py-2.5 pl-9 pr-3 text-sm" />
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {LEVELS.map((item) => (
                  <button key={item} type="button" onClick={() => setLevel(item)} className={`rounded-lg px-2.5 py-1.5 text-xs font-semibold transition ${level === item ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300"}`}>{item}</button>
                ))}
              </div>
              <div className="mt-4 max-h-[520px] space-y-2 overflow-y-auto pr-1">
                {loadingMaterials ? <div className="flex justify-center py-12"><Loader2 className="animate-spin text-blue-500" /></div> : filteredMaterials.length ? filteredMaterials.map((material) => (
                  <button type="button" key={material.id} disabled={recording} onClick={() => selectMaterial(material)} className={`w-full rounded-2xl border p-4 text-left transition ${selectedMaterial?.id === material.id ? "border-blue-500 bg-blue-50 shadow-sm dark:bg-blue-950/30" : "border-slate-200 bg-white hover:border-blue-300 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:hover:bg-slate-800"} disabled:cursor-not-allowed disabled:opacity-60`}>
                    <div className="flex items-start justify-between gap-3"><p className="font-semibold text-slate-800 dark:text-slate-100">{material.title}</p><span className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-bold text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300">{material.level}</span></div>
                    <p className="mt-2 flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400"><Clock3 size={13} /> {material.duration}</p>
                  </button>
                )) : <p className="py-10 text-center text-sm text-slate-400">没有匹配的材料</p>}
              </div>
            </aside>

            <main className="min-w-0 space-y-6">
              <section className="student-card p-5 md:p-6">
                {loadingDetail ? <div className="flex min-h-56 items-center justify-center gap-2 text-slate-500"><Loader2 className="animate-spin" /> 加载练习内容…</div> : materialDetail ? (
                  <>
                    <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
                      <div><p className="text-xs font-bold uppercase tracking-[0.2em] text-blue-600">Listening lab</p><h2 className="mt-1 text-2xl font-black text-slate-900 dark:text-white">{materialDetail.title}</h2><p className="mt-1 text-sm text-slate-500">{materialDetail.level} · {materialDetail.duration}</p></div>
                      <select value={playbackRate} onChange={(event) => setPlaybackRate(Number(event.target.value))} className="student-input rounded-xl px-3 py-2 text-sm" aria-label="播放速度"><option value={0.75}>0.75× 慢速</option><option value={1}>1.0× 正常</option><option value={1.25}>1.25× 快速</option></select>
                    </div>
                    <div className="mt-5 rounded-2xl border border-sky-100 bg-gradient-to-br from-sky-50 to-indigo-50 p-4 dark:border-sky-900 dark:from-sky-950/40 dark:to-indigo-950/30">
                      {!audioFailed && materialDetail.audioUrl ? (
                        <audio ref={audioRef} src={materialDetail.audioUrl} controls className="w-full" onError={() => setAudioFailed(true)} onLoadedMetadata={() => { if (audioRef.current) audioRef.current.playbackRate = playbackRate; }} />
                      ) : (
                        <div className="flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center"><div><p className="font-semibold text-slate-800 dark:text-slate-100">原始音频暂不可用</p><p className="mt-1 text-sm text-slate-500 dark:text-slate-400">可以使用浏览器内置德语语音完成精听和跟读。</p></div><button type="button" onClick={speakScript} className="student-action-primary flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-bold">{ttsPlaying ? <><Pause size={17} /> 停止朗读</> : <><Play size={17} /> 德语朗读</>}</button></div>
                      )}
                      {!audioFailed && materialDetail.audioUrl && <button type="button" onClick={speakScript} className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-blue-700 hover:text-blue-800 dark:text-blue-300"><Volume2 size={16} /> {ttsPlaying ? "停止备用朗读" : "使用系统德语朗读"}</button>}
                    </div>
                    <div className="mt-4 rounded-2xl border border-slate-200 p-4 dark:border-slate-700">
                      <button type="button" onClick={() => setShowScript((value) => !value)} className="flex w-full items-center justify-between text-left"><span className="flex items-center gap-2 font-semibold text-slate-800 dark:text-slate-100"><BookOpen size={18} /> 听力原文</span><span className="text-sm font-semibold text-blue-600">{showScript ? "隐藏原文" : "完成精听后查看"}</span></button>
                      {showScript ? <p className="mt-4 whitespace-pre-wrap rounded-xl bg-slate-50 p-4 leading-8 text-slate-700 dark:bg-slate-900 dark:text-slate-300">{materialDetail.script}</p> : <div className="mt-4 rounded-xl border border-dashed border-slate-300 py-6 text-center text-sm text-slate-400 dark:border-slate-700">原文已隐藏，先尝试听懂关键信息</div>}
                    </div>
                  </>
                ) : <div className="py-16 text-center text-slate-400">请从左侧选择一篇材料</div>}
              </section>

              {materialDetail && (
                <section className="student-card p-5 md:p-6">
                  <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center"><div><p className="text-xs font-bold uppercase tracking-[0.2em] text-violet-600">Speaking studio</p><h2 className="mt-1 text-xl font-black text-slate-900 dark:text-white">跟读录音与智能评测</h2></div><div className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-bold ${recording ? "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300" : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300"}`}><span className={`h-2 w-2 rounded-full ${recording ? "animate-pulse bg-rose-500" : "bg-slate-400"}`} />{recording ? `录音中 ${formatSeconds(recordingSeconds)}` : "最长 02:00"}</div></div>
                  {!window.isSecureContext && <div className="mt-4 flex gap-2 rounded-xl bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-950/30 dark:text-amber-300"><AlertCircle className="mt-0.5 shrink-0" size={17} />当前不是 HTTPS 安全页面，浏览器可能禁用麦克风。可先上传录音；正式部署请配置 HTTPS。</div>}
                  <div className="mt-5 grid gap-4 md:grid-cols-[220px_minmax(0,1fr)]">
                    <div className="flex flex-col items-center justify-center rounded-2xl bg-slate-50 p-5 dark:bg-slate-900">
                      <button type="button" onClick={recording ? stopRecording : startRecording} disabled={submitting} className={`flex h-24 w-24 items-center justify-center rounded-full text-white shadow-lg transition hover:scale-105 disabled:opacity-50 ${recording ? "bg-rose-600 shadow-rose-300/50" : "bg-gradient-to-br from-violet-500 to-blue-600 shadow-blue-300/50"}`} aria-label={recording ? "结束录音" : "开始录音"}>{recording ? <Square size={34} fill="currentColor" /> : <Mic size={38} />}</button>
                      <p className="mt-3 text-sm font-semibold text-slate-700 dark:text-slate-200">{recording ? "点击结束录音" : "点击开始跟读"}</p>
                      <button type="button" disabled={recording || submitting} onClick={() => fileInputRef.current?.click()} className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 disabled:opacity-40"><Upload size={14} /> 上传已有录音</button>
                      <input ref={fileInputRef} type="file" accept="audio/*" className="hidden" onChange={handleAudioUpload} />
                    </div>
                    <div className="min-w-0 space-y-4">
                      {recordingUrl ? (
                        <div className="rounded-2xl border border-slate-200 p-4 dark:border-slate-700"><div className="mb-3 flex items-center justify-between"><p className="flex items-center gap-2 font-semibold text-slate-800 dark:text-slate-100"><Waves size={18} className="text-violet-500" /> 我的录音</p><button type="button" onClick={resetAttempt} disabled={submitting} className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-rose-600"><RotateCcw size={14} /> 重录</button></div><audio src={recordingUrl} controls className="w-full" onLoadedMetadata={(event) => { if (Number.isFinite(event.currentTarget.duration)) setRecordingSeconds(event.currentTarget.duration); }} /><div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500"><span className="rounded-full bg-slate-100 px-2.5 py-1 dark:bg-slate-800">时长 {formatSeconds(recordingSeconds)}</span><span className="rounded-full bg-slate-100 px-2.5 py-1 dark:bg-slate-800">停顿 {pauseCount} 次</span><span className="rounded-full bg-slate-100 px-2.5 py-1 dark:bg-slate-800">已采集节奏特征</span></div></div>
                      ) : <div className="flex min-h-32 items-center justify-center rounded-2xl border border-dashed border-slate-300 text-sm text-slate-400 dark:border-slate-700">录音完成后可在这里试听</div>}
                      <div><div className="mb-2 flex items-center justify-between gap-3"><label htmlFor="speaking-transcript" className="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-200"><Languages size={17} /> 德语语音转写</label><span className="text-xs text-slate-400">{speechRecognitionSupported ? "自动识别，可手动校正" : "请手动填写"}</span></div><textarea id="speaking-transcript" rows={4} disabled={recording || submitting} value={`${transcript}${liveTranscript ? ` ${liveTranscript}` : ""}`} onChange={(event) => { setTranscript(event.target.value); finalTranscriptRef.current = event.target.value; setLiveTranscript(""); }} placeholder="录音时将自动识别；如果浏览器不支持识别，请输入你实际朗读的德语内容。" className="student-input w-full resize-y rounded-xl px-3 py-3 text-sm leading-6" /></div>
                      <button type="button" onClick={submitEvaluation} disabled={!recordingBlob || recording || submitting} className="student-action-primary flex w-full items-center justify-center gap-2 rounded-xl px-5 py-3 font-bold disabled:cursor-not-allowed disabled:opacity-50">{submitting ? <><Loader2 className="animate-spin" size={19} /> 正在分析录音…</> : <><Sparkles size={19} /> 开始智能评测</>}</button>
                    </div>
                  </div>
                </section>
              )}

              {evaluation && (
                <section className="student-card overflow-hidden">
                  <div className="border-b border-slate-200 bg-gradient-to-r from-emerald-50 to-blue-50 p-5 dark:border-slate-700 dark:from-emerald-950/30 dark:to-blue-950/30 md:p-6"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center"><div><p className="text-sm font-bold text-emerald-600">评测完成</p><h2 className="mt-1 text-2xl font-black text-slate-900 dark:text-white">本次综合得分</h2></div><div className={`text-5xl font-black ${scoreTone(evaluation.totalScore)}`}>{evaluation.totalScore}<span className="text-lg"> / 100</span></div></div></div>
                  <div className="p-5 md:p-6">
                    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                      {[{ label: "转写准确度", score: evaluation.accuracyScore }, { label: "发音准确度", score: evaluation.pronunciationScore }, { label: "流利度", score: evaluation.fluencyScore }, { label: "语调节奏", score: evaluation.intonationScore }].map(({ label: itemLabel, score }) => (
                        <div key={itemLabel} className="rounded-2xl border border-slate-200 p-4 dark:border-slate-700"><Activity size={19} className="text-blue-500" /><p className={`mt-3 text-3xl font-black ${scoreTone(score)}`}>{score}</p><p className="mt-1 text-xs text-slate-500">{itemLabel}</p></div>
                      ))}
                    </div>
                    <div className="mt-5 grid gap-4 lg:grid-cols-2"><div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-900"><h3 className="font-bold text-slate-800 dark:text-slate-100">详细分析</h3><p className="mt-2 whitespace-pre-wrap text-sm leading-7 text-slate-600 dark:text-slate-300">{evaluation.analysis}</p></div><div className="rounded-2xl bg-blue-50 p-4 dark:bg-blue-950/30"><h3 className="font-bold text-blue-800 dark:text-blue-200">下一步建议</h3><p className="mt-2 whitespace-pre-wrap text-sm leading-7 text-blue-700 dark:text-blue-300">{evaluation.suggestion}</p></div></div>
                    <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-500"><span className="rounded-full bg-slate-100 px-3 py-1.5 dark:bg-slate-800">语速 {evaluation.wordsPerMinute} 词/分钟</span>{evaluation.missingWords?.length > 0 && <span className="rounded-full bg-amber-100 px-3 py-1.5 text-amber-700 dark:bg-amber-950 dark:text-amber-300">建议复习：{evaluation.missingWords.join("、")}</span>}</div>
                  </div>
                </section>
              )}

              <section className="student-card p-5 md:p-6">
                <div className="flex items-center justify-between"><div className="flex items-center gap-2"><History size={20} className="text-slate-500" /><h2 className="font-black text-slate-900 dark:text-white">近期训练记录</h2></div><BarChart3 size={20} className="text-blue-500" /></div>
                {loadingHistory ? <div className="flex justify-center py-10"><Loader2 className="animate-spin text-blue-500" /></div> : history.length ? (
                  <div className="mt-4 space-y-3">{history.map((item) => (
                    <div key={item.id} className="flex flex-col gap-3 rounded-2xl border border-slate-200 p-4 dark:border-slate-700 sm:flex-row sm:items-center sm:justify-between"><div className="min-w-0"><div className="flex items-center gap-2"><p className="truncate font-semibold text-slate-800 dark:text-slate-100">{item.materialTitle}</p><span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-500 dark:bg-slate-800">{item.level}</span></div><p className="mt-1 text-xs text-slate-400">{formatDate(item.evaluatedAt)}</p></div><div className="flex items-center gap-5 text-center"><div><p className={`text-xl font-black ${scoreTone(item.totalScore)}`}>{Math.round(item.totalScore)}</p><p className="text-[11px] text-slate-400">综合</p></div><div className="hidden sm:block"><p className="text-sm font-bold text-slate-600 dark:text-slate-300">{Math.round(item.pronunciationScore)}</p><p className="text-[11px] text-slate-400">发音</p></div><div className="hidden sm:block"><p className="text-sm font-bold text-slate-600 dark:text-slate-300">{Math.round(item.fluencyScore)}</p><p className="text-[11px] text-slate-400">流利</p></div></div></div>
                  ))}</div>
                ) : <div className="mt-4 rounded-2xl border border-dashed border-slate-300 py-10 text-center text-sm text-slate-400 dark:border-slate-700">完成第一次跟读后，记录会显示在这里</div>}
              </section>
            </main>
          </div>
        </div>
      </div>
    </StudentLayout>
  );
};

export default ListeningSpeaking;
