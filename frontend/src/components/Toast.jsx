import React, { useState, useCallback, createContext, useContext } from 'react';
import { CheckCircle, XCircle, Info, X } from 'lucide-react';

// ---------------------------------------------------------------
// Toast 通知组件 — 替代 alert() 弹窗
// ---------------------------------------------------------------

const ToastContext = createContext(null);

/**
 * 使用方法:
 *   1. 在 App 外层包裹 <ToastProvider>
 *   2. 组件内部调用 const toast = useToast();
 *   3. toast.success('操作成功');  toast.error('操作失败');  toast.info('提示');
 */
export const useToast = () => {
    const ctx = useContext(ToastContext);
    if (!ctx) throw new Error('useToast 必须在 <ToastProvider> 内部使用');
    return ctx;
};

export const ToastProvider = ({ children }) => {
    const [toasts, setToasts] = useState([]);

    const addToast = useCallback((message, type = 'info', duration = 3500) => {
        const id = Date.now() + Math.random();
        setToasts(prev => [...prev, { id, message, type }]);
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id));
        }, duration);
    }, []);

    const removeToast = useCallback((id) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    const toast = {
        success: (msg, dur) => addToast(msg, 'success', dur),
        error: (msg, dur) => addToast(msg, 'error', dur ?? 5000),
        info: (msg, dur) => addToast(msg, 'info', dur),
    };

    return (
        <ToastContext.Provider value={toast}>
            {children}
            {/* Toast 渲染容器 */}
            <div className="fixed top-6 right-6 z-[9999] flex flex-col gap-3 pointer-events-none">
                {toasts.map(t => (
                    <ToastItem key={t.id} toast={t} onClose={() => removeToast(t.id)} />
                ))}
            </div>
        </ToastContext.Provider>
    );
};

// 单条 Toast 样式
const STYLES = {
    success: {
        bg: 'bg-green-50 dark:bg-green-900/30 border-green-200',
        icon: <CheckCircle size={20} className="text-green-600 shrink-0" />,
        text: 'text-green-800',
    },
    error: {
        bg: 'bg-red-50 dark:bg-red-900/30 border-red-200',
        icon: <XCircle size={20} className="text-red-600 shrink-0" />,
        text: 'text-red-800',
    },
    info: {
        bg: 'bg-blue-50 dark:bg-blue-900/30 border-blue-200',
        icon: <Info size={20} className="text-blue-600 dark:text-blue-400 shrink-0" />,
        text: 'text-blue-800',
    },
};

const ToastItem = ({ toast, onClose }) => {
    const style = STYLES[toast.type] || STYLES.info;
    return (
        <div
            className={`pointer-events-auto flex items-start gap-3 px-5 py-4 rounded-xl border shadow-lg backdrop-blur-sm max-w-sm animate-slide-in-right ${style.bg}`}
            role="alert"
        >
            {style.icon}
            <p className={`text-sm font-medium leading-relaxed flex-1 ${style.text}`}>{toast.message}</p>
            <button onClick={onClose} className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:text-gray-400 shrink-0">
                <X size={16} />
            </button>
        </div>
    );
};

export default ToastProvider;
