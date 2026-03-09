import React, { useState } from 'react';
import { X, Lock, Key, Save, Loader2 } from 'lucide-react';
import request from '../api/request';
import { useToast } from './Toast';

const PasswordChangeModal = ({ isOpen, onClose }) => {
    const toast = useToast();
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);

    if (!isOpen) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!oldPassword || !newPassword || !confirmPassword) {
            toast.error('请填写所有密码字段');
            return;
        }

        if (newPassword !== confirmPassword) {
            toast.error('两次输入的新密码不一致');
            return;
        }

        if (newPassword.length < 6) {
            toast.error('新密码长度不能小于6位');
            return;
        }

        setLoading(true);
        try {
            const response = await request.put('/api/user/password', {
                oldPassword,
                newPassword
            });

            if (response.data.code === 200) {
                toast.success('密码修改成功，请使用新密码重新登录');
                // 延迟关闭并登出，让用户重新登录
                setTimeout(() => {
                    onClose();
                    localStorage.removeItem('authToken');
                    localStorage.removeItem('userInfo');
                    window.location.href = '/';
                }, 1500);
            } else {
                toast.error(response.data.message || '密码修改失败');
            }
        } catch (error) {
            console.error('修改密码出错:', error);
            const msg = error?.response?.data?.message || '网络或服务器错误';
            toast.error(msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md overflow-hidden relative" onClick={(e) => e.stopPropagation()}>
                <div className="flex justify-between items-center p-6 border-b border-gray-100 dark:border-gray-700">
                    <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                        <Key className="text-indigo-600 dark:text-indigo-400" /> 修改密码
                    </h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
                        <X size={20} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-4 text-left">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">原密码</label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <Lock size={16} className="text-gray-400" />
                            </div>
                            <input
                                type="password"
                                value={oldPassword}
                                onChange={(e) => setOldPassword(e.target.value)}
                                className="pl-10 w-full rounded-xl border border-gray-200 dark:border-gray-600 px-4 py-2.5 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                placeholder="请输入原密码"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">新密码</label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <Key size={16} className="text-gray-400" />
                            </div>
                            <input
                                type="password"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                className="pl-10 w-full rounded-xl border border-gray-200 dark:border-gray-600 px-4 py-2.5 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                placeholder="请设置新密码（至少6位）"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">确认新密码</label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <Lock size={16} className="text-gray-400" />
                            </div>
                            <input
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                className="pl-10 w-full rounded-xl border border-gray-200 dark:border-gray-600 px-4 py-2.5 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                placeholder="请再次输入新密码"
                            />
                        </div>
                    </div>

                    <div className="pt-4 flex justify-end gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-5 py-2.5 text-sm font-medium text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-xl transition-colors"
                        >
                            取消
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className={`px-5 py-2.5 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-colors flex items-center gap-2 ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
                        >
                            {loading ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                            确认修改
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default PasswordChangeModal;
