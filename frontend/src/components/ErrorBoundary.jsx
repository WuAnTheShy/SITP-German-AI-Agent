import React from "react";

/**
 * 捕获子树渲染错误，避免 React 18 下未捕获异常导致整页空白且无任何提示。
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error("[ErrorBoundary]", error, info?.componentStack);
  }

  render() {
    if (this.state.hasError) {
      const msg = this.state.error?.message || String(this.state.error);
      return (
        <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-100">
          <h1 className="text-lg font-semibold mb-2">页面渲染出错</h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-4 text-center max-w-lg">
            这通常是前端代码异常或浏览器缓存了旧脚本。请打开开发者工具 (F12) 查看 Console，或尝试强制刷新 (Ctrl+Shift+R)。
          </p>
          <pre className="text-xs text-red-600 dark:text-red-400 max-w-full overflow-auto p-3 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 mb-4">
            {msg}
          </pre>
          <button
            type="button"
            className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm hover:bg-indigo-500"
            onClick={() => window.location.reload()}
          >
            刷新页面
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
