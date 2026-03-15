import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import request from '../../api/request';
import { LogOut, Users, BookOpen, Loader2, Shield, Plus, Pencil } from 'lucide-react';
import { API_ADMIN_TEACHERS, API_ADMIN_CLASSES } from '../../api/config';

const AdminDashboard = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [teachers, setTeachers] = useState([]);
    const [classes, setClasses] = useState([]);
    const [error, setError] = useState('');
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [editingClass, setEditingClass] = useState(null);
    const [submitLoading, setSubmitLoading] = useState(false);
    const [formError, setFormError] = useState('');

    const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
    const adminName = userInfo.name || '管理员';

    const fetchData = useCallback(async () => {
        setError('');
        try {
            const [teachersRes, classesRes] = await Promise.all([
                request.get(API_ADMIN_TEACHERS),
                request.get(API_ADMIN_CLASSES),
            ]);
            setTeachers(Array.isArray(teachersRes.data) ? teachersRes.data : []);
            setClasses(Array.isArray(classesRes.data) ? classesRes.data : []);
        } catch (err) {
            console.error('管理员数据加载失败:', err);
            setError(err.response?.data?.detail || err.message || '加载失败');
            setTeachers([]);
            setClasses([]);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        setLoading(true);
        fetchData();
    }, [fetchData]);

    const handleLogout = () => {
        localStorage.removeItem('authToken');
        localStorage.removeItem('userInfo');
        navigate('/teacher/login');
    };

    const handleCreateClass = async (e) => {
        e.preventDefault();
        const form = e.target;
        const class_code = (form.class_code?.value || '').trim();
        const class_name = (form.class_name?.value || '').trim();
        const grade = (form.grade?.value || '').trim() || null;
        const teacher_user_id = parseInt(form.teacher_id?.value, 10);
        setFormError('');
        if (!class_code || !class_name || !teacher_user_id) {
            setFormError('请填写班级代码、班级名称并选择负责教师');
            return;
        }
        setSubmitLoading(true);
        try {
            await request.post(API_ADMIN_CLASSES, { class_code, class_name, grade, teacher_user_id });
            setShowCreateModal(false);
            form.reset();
            fetchData();
        } catch (err) {
            setFormError(err.response?.data?.detail || err.message || '创建失败');
        } finally {
            setSubmitLoading(false);
        }
    };

    const openEditModal = (c) => {
        setEditingClass(c);
        setFormError('');
        setShowEditModal(true);
    };

    const handleEditClass = async (e) => {
        e.preventDefault();
        if (!editingClass) return;
        const form = e.target;
        const class_name = (form.class_name?.value || '').trim();
        const grade = (form.grade?.value || '').trim() || null;
        const teacher_user_id = parseInt(form.teacher_id?.value, 10);
        setFormError('');
        if (!class_name) {
            setFormError('请填写班级名称');
            return;
        }
        setSubmitLoading(true);
        try {
            await request.put(`${API_ADMIN_CLASSES}/${editingClass.id}`, {
                class_name,
                grade: grade || undefined,
                teacher_user_id,
            });
            setShowEditModal(false);
            setEditingClass(null);
            fetchData();
        } catch (err) {
            setFormError(err.response?.data?.detail || err.message || '保存失败');
        } finally {
            setSubmitLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-900">
                <Loader2 size={40} className="text-indigo-600 dark:text-indigo-400 animate-spin mb-4" />
                <p className="text-gray-500 dark:text-gray-400 font-medium">正在加载...</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4 md:p-8">
            <div className="max-w-5xl mx-auto space-y-6">
                {/* 顶部 */}
                <div className="flex flex-wrap items-center justify-between gap-4">
                    <div>
                        <h1 className="text-xl md:text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-3">
                            <Shield className="text-amber-500 dark:text-amber-400 shrink-0" />
                            管理员工作台
                        </h1>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">欢迎，{adminName}。</p>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/10 transition-colors"
                    >
                        <LogOut size={18} />
                        退出登录
                    </button>
                </div>

                {error && (
                    <div className="rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 text-sm">
                        {error}
                    </div>
                )}

                {/* 教师列表 */}
                <section className="rounded-2xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 overflow-hidden">
                    <div className="px-4 py-3 border-b border-gray-200 dark:border-white/10 flex items-center gap-2">
                        <Users className="text-indigo-500 dark:text-indigo-400" size={20} />
                        <h2 className="font-semibold text-gray-900 dark:text-gray-100">教师列表</h2>
                    </div>
                    <div className="p-4">
                        {teachers.length === 0 ? (
                            <p className="text-sm text-gray-500 dark:text-gray-400">暂无教师账号</p>
                        ) : (
                            <ul className="space-y-2">
                                {teachers.map((t) => (
                                    <li key={t.id} className="flex items-center gap-3 py-2 px-3 rounded-lg bg-gray-50 dark:bg-white/5 text-sm">
                                        <span className="font-mono text-gray-500 dark:text-gray-400 w-24">ID {t.id}</span>
                                        <span className="font-medium text-gray-800 dark:text-gray-200">{t.display_name}</span>
                                        <span className="text-gray-500 dark:text-gray-400">({t.username})</span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                </section>

                {/* 班级列表 */}
                <section className="rounded-2xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 overflow-hidden">
                    <div className="px-4 py-3 border-b border-gray-200 dark:border-white/10 flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                            <BookOpen className="text-indigo-500 dark:text-indigo-400" size={20} />
                            <h2 className="font-semibold text-gray-900 dark:text-gray-100">班级列表</h2>
                        </div>
                        <button
                            type="button"
                            onClick={() => { setShowCreateModal(true); setFormError(''); }}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors"
                        >
                            <Plus size={16} />
                            新建班级
                        </button>
                    </div>
                    <div className="p-4">
                        {classes.length === 0 ? (
                            <p className="text-sm text-gray-500 dark:text-gray-400">暂无班级，可点击「新建班级」添加。</p>
                        ) : (
                            <ul className="space-y-2">
                                {classes.map((c) => (
                                    <li key={c.id} className="flex flex-wrap items-center gap-2 py-2 px-3 rounded-lg bg-gray-50 dark:bg-white/5 text-sm group">
                                        <span className="font-mono text-gray-500 dark:text-gray-400">{c.class_code}</span>
                                        <span className="font-medium text-gray-800 dark:text-gray-200">{c.class_name}</span>
                                        {c.grade && <span className="text-gray-500 dark:text-gray-400">({c.grade})</span>}
                                        <span className="text-gray-500 dark:text-gray-400">— 负责教师: {c.teacher_display_name ?? c.teacher_username ?? `ID ${c.teacher_user_id}`}</span>
                                        <button
                                            type="button"
                                            onClick={() => openEditModal(c)}
                                            className="ml-auto inline-flex items-center gap-1 px-2 py-1 rounded-md text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity"
                                        >
                                            <Pencil size={12} />
                                            编辑
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                </section>
            </div>

            {/* 新建班级弹窗 */}
            {showCreateModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={() => !submitLoading && setShowCreateModal(false)}>
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md p-6" onClick={e => e.stopPropagation()}>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">新建班级</h3>
                        <form onSubmit={handleCreateClass}>
                            {formError && <p className="text-sm text-red-600 dark:text-red-400 mb-3">{formError}</p>}
                            <div className="space-y-3">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">班级代码</label>
                                    <input name="class_code" type="text" required placeholder="如 SE-2026-1" className="input-glow w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-gray-100 text-sm" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">班级名称</label>
                                    <input name="class_name" type="text" required placeholder="如 软件工程(一)班" className="input-glow w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-gray-100 text-sm" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">年级（选填）</label>
                                    <input name="grade" type="text" placeholder="如 2026" className="input-glow w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-gray-100 text-sm" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">负责教师</label>
                                    <select name="teacher_id" required className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-gray-100 text-sm">
                                        <option value="">请选择</option>
                                        {teachers.map(t => <option key={t.id} value={t.id}>{t.display_name} ({t.username})</option>)}
                                    </select>
                                </div>
                            </div>
                            <div className="flex gap-2 mt-6">
                                <button type="button" onClick={() => !submitLoading && setShowCreateModal(false)} className="flex-1 py-2 rounded-lg border border-gray-200 dark:border-white/10 text-gray-700 dark:text-gray-300 text-sm font-medium">取消</button>
                                <button type="submit" disabled={submitLoading} className="flex-1 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium disabled:opacity-50">{submitLoading ? '提交中…' : '创建'}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* 编辑班级弹窗 */}
            {showEditModal && editingClass && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={() => !submitLoading && setShowEditModal(false)}>
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md p-6" onClick={e => e.stopPropagation()}>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">编辑班级 · {editingClass.class_code}</h3>
                        <form onSubmit={handleEditClass}>
                            {formError && <p className="text-sm text-red-600 dark:text-red-400 mb-3">{formError}</p>}
                            <div className="space-y-3">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">班级名称</label>
                                    <input name="class_name" type="text" required defaultValue={editingClass.class_name} className="input-glow w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-gray-100 text-sm" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">年级（选填）</label>
                                    <input name="grade" type="text" defaultValue={editingClass.grade ?? ''} placeholder="如 2026" className="input-glow w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-gray-100 text-sm" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">负责教师</label>
                                    <select name="teacher_id" required defaultValue={editingClass.teacher_user_id} className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-gray-100 text-sm">
                                        {teachers.map(t => <option key={t.id} value={t.id}>{t.display_name} ({t.username})</option>)}
                                    </select>
                                </div>
                            </div>
                            <div className="flex gap-2 mt-6">
                                <button type="button" onClick={() => !submitLoading && setShowEditModal(false)} className="flex-1 py-2 rounded-lg border border-gray-200 dark:border-white/10 text-gray-700 dark:text-gray-300 text-sm font-medium">取消</button>
                                <button type="submit" disabled={submitLoading} className="flex-1 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium disabled:opacity-50">{submitLoading ? '保存中…' : '保存'}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminDashboard;
