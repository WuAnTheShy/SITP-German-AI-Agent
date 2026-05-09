import { CheckCircle2, Loader2, Search, Wrench, BookOpen } from "lucide-react";

/**
 * Agent 流式进度展示。
 *
 * Props:
 *   stages: Array<{ type, label, status, summary }>
 *     type:    'rag' | 'tool' | 'thinking'
 *     label:   显示文字
 *     status:  'running' | 'done' | 'failed'
 *     summary: 完成后显示的摘要(可选)
 */
export default function AgentProgress({ stages = [] }) {
  if (!stages.length) return null;

  return (
    <div className="mb-2 space-y-1">
      {stages.map((stage, i) => (
        <div
          key={i}
          className="flex items-center gap-2 text-xs px-2 py-1 rounded-md bg-slate-50 dark:bg-slate-800/40 border border-slate-200/50 dark:border-slate-700/50"
        >
          <StageIcon type={stage.type} status={stage.status} />
          <span className="text-slate-600 dark:text-slate-300">
            {stage.label}
          </span>
          {stage.summary && (
            <span className="text-slate-400 dark:text-slate-500 truncate flex-1">
              · {stage.summary}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

function StageIcon({ type, status }) {
  if (status === "running") {
    return (
      <Loader2 size={12} className="animate-spin text-blue-500 shrink-0" />
    );
  }
  if (status === "failed") {
    return <span className="text-red-500 shrink-0">✗</span>;
  }
  // done
  if (type === "rag") {
    return <BookOpen size={12} className="text-orange-500 shrink-0" />;
  }
  if (type === "tool") {
    return <Wrench size={12} className="text-blue-500 shrink-0" />;
  }
  return <CheckCircle2 size={12} className="text-green-500 shrink-0" />;
}
