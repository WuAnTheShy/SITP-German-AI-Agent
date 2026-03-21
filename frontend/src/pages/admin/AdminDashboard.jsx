import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import request from '../../api/request';
import { LogOut, Users, BookOpen, Loader2, Shield, Plus, Pencil, Settings, UserPlus, Trash2, CheckCircle, XCircle, Search, RefreshCw, KeyRound } from 'lucide-react';
import { useToast } from '../../components/Toast';
import { sha256Hex } from '../../utils/security';
import {
    API_ADMIN_TEACHERS,
    API_ADMIN_CLASSES,
    API_ADMIN_SETTINGS,
    API_ADMIN_PENDING_TEACHERS,
    API_ADMIN_APPROVE_TEACHER,
    API_ADMIN_REJECT_TEACHER,
    API_ADMIN_DELETE_CLASS,
    API_ADMIN_UPDATE_TEACHER,
    API_ADMIN_DELETE_TEACHER,
    API_ADMIN_STUDENTS,
    API_ADMIN_UPDATE_STUDENT,
    API_ADMIN_DELETE_STUDENT,
    API_ADMIN_RESET_USER_PASSWORD,
} from '../../api/config';

const AdminDashboard = () => {
    const navigate = useNavigate();
    const toast = useToast();
    const [loading, setLoading] = useState(true);
    const [teachers, setTeachers] = useState([]);
    const [pendingTeachers, setPendingTeachers] = useState([]);
    const [classes, setClasses] = useState([]);
    const [students, setStudents] = useState([]);
    const [settings, setSettings] = useState({ REQUIRE_TEACHER_APPROVAL: false, REQUIRE_STUDENT_APPROVAL: false });
    const [error, setError] = useState('');
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [editingClass, setEditingClass] = useState(null);
    const [editingStudent, setEditingStudent] = useState(null);
    const [submitLoading, setSubmitLoading] = useState(false);
    const [formError, setFormError] = useState('');
    const [refreshing, setRefreshing] = useState(false);
    const [resettingAccount, setResettingAccount] = useState(null);
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [teacherKeyword, setTeacherKeyword] = useState('');
    const [studentKeyword, setStudentKeyword] = useState('');
    const [studentStatusFilter, setStudentStatusFilter] = useState('all');
    const [classFilter, setClassFilter] = useState('all');

    const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
    const adminName = userInfo.name || '管理员';
    const activeTeacherCount = teachers.filter((t) => t.is_active).length;
    const unassignedStudentCount = students.filter((s) => !s.class_id).length;

    const statusLabel = (status) => {
        if (status === 'approved') return '审核通过';
        if (status === 'pending') return '待审核';
        if (status === 'rejected') return '已拒绝';
        return status || '未知';
    };

    const filteredTeachers = useMemo(() => {
        const kw = teacherKeyword.trim().toLowerCase();
        if (!kw) return teachers;
        return teachers.filter((t) =>
            String(t.display_name || '').toLowerCase().includes(kw) ||
            String(t.username || '').toLowerCase().includes(kw) ||
            String(t.id || '').toLowerCase().includes(kw)
        );
    }, [teachers, teacherKeyword]);

    const filteredStudents = useMemo(() => {
        const kw = studentKeyword.trim().toLowerCase();
        return students.filter((s) => {
            const hitKeyword = !kw ||
                String(s.name || '').toLowerCase().includes(kw) ||
                String(s.uid || '').toLowerCase().includes(kw);
            const hitStatus = studentStatusFilter === 'all' || s.status === studentStatusFilter;
            const hitClass = classFilter === 'all' || String(s.class_id ?? 'none') === classFilter;
            return hitKeyword && hitStatus && hitClass;
        });
    }, [students, studentKeyword, studentStatusFilter, classFilter]);

    const fetchData = useCallback(async (showToast = false) => {
        setError('');
        if (showToast) setRefreshing(true);
        try {
            const [teachersRes, classesRes, settingsRes, pendingRes, studentsRes] = await Promise.all([
                request.get(API_ADMIN_TEACHERS),
                request.get(API_ADMIN_CLASSES),
                request.get(API_ADMIN_SETTINGS),
                request.get(API_ADMIN_PENDING_TEACHERS),
                request.get(API_ADMIN_STUDENTS),
            ]);
            setTeachers(Array.isArray(teachersRes.data) ? teachersRes.data : []);
            setClasses(Array.isArray(classesRes.data) ? classesRes.data : []);
            setSettings(settingsRes.data || { REQUIRE_TEACHER_APPROVAL: false, REQUIRE_STUDENT_APPROVAL: false });
            setPendingTeachers(Array.isArray(pendingRes.data) ? pendingRes.data : []);
            setStudents(Array.isArray(studentsRes.data) ? studentsRes.data : []);
            if (showToast) toast.success('数据已刷新');
        } catch (err) {
            console.error('管理员数据加载失败:', err);
            setError(err.response?.data?.detail || err.message || '加载失败');
            setTeachers([]);
            setClasses([]);
            setPendingTeachers([]);
            setStudents([]);
            if (showToast) toast.error('刷新失败，请稍后重试');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, [toast]);

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
            toast.success('班级创建成功');
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
            toast.success('班级信息已更新');
        } catch (err) {
            setFormError(err.response?.data?.detail || err.message || '保存失败');
        } finally {
            setSubmitLoading(false);
        }
    };

    const handleDeleteClass = async (id) => {
        if(!window.confirm('确认删除该班级？\n\n注意：班级删除后无法恢复，建议先确认是否需要保留班级历史信息。')) return;
        try {
            await request.delete(API_ADMIN_DELETE_CLASS(id));
            fetchData();
            toast.success('班级已删除');
        } catch (err) {
            setError(err.response?.data?.detail || err.message || '删除失败');
            toast.error(err.response?.data?.detail || err.message || '删除失败');
        }
    };

    const toggleSetting = async (key, value) => {
        try {
            await request.put(API_ADMIN_SETTINGS, { [key]: value });
            setSettings(prev => ({ ...prev, [key]: value }));
            toast.success('系统设置已保存');
        } catch (err) {
            setError(err.response?.data?.detail || err.message || '设置保存失败');
            toast.error(err.response?.data?.detail || err.message || '设置保存失败');
        }
    };

    const handleApproveTeacher = async (id) => {
        try {
            await request.put(API_ADMIN_APPROVE_TEACHER(id));
            fetchData();
            toast.success('教师审核通过');
        } catch (err) {
            setError(err.response?.data?.detail || err.message || '审批失败');
            toast.error(err.response?.data?.detail || err.message || '审批失败');
        }
    };

    const handleRejectTeacher = async (id) => {
        if(!window.confirm('确定拒绝并删除该教师注册申请吗？')) return;
        try {
            await request.put(API_ADMIN_REJECT_TEACHER(id));
            fetchData();
            toast.info('已拒绝该教师申请');
        } catch (err) {
            setError(err.response?.data?.detail || err.message || '拒绝失败');
            toast.error(err.response?.data?.detail || err.message || '拒绝失败');
        }
    };

    const handleUpdateTeacher = async (id, payload) => {
        try {
            await request.put(API_ADMIN_UPDATE_TEACHER(id), payload);
            fetchData();
            toast.success('教师信息已更新');
        } catch (err) {
            setError(err.response?.data?.detail || err.message || '教师信息更新失败');
            toast.error(err.response?.data?.detail || err.message || '教师信息更新失败');
        }
    };

    const handleDeleteTeacher = async (id) => {
        if (!window.confirm('确认删除该教师账号？\n\n如果该教师仍负责班级，系统会阻止删除。')) return;
        try {
            await request.delete(API_ADMIN_DELETE_TEACHER(id));
            fetchData();
            toast.success('教师账号已删除');
        } catch (err) {
            setError(err.response?.data?.detail || err.message || '教师删除失败');
            toast.error(err.response?.data?.detail || err.message || '教师删除失败');
        }
    };

    const openEditStudentModal = (student) => {
        setEditingStudent(student);
        setFormError('');
    };

    const handleEditStudent = async (e) => {
        e.preventDefault();
        if (!editingStudent) return;

        const form = e.target;
        const payload = {
            name: (form.name?.value || '').trim(),
            class_id: form.class_id?.value === '' ? null : parseInt(form.class_id?.value, 10),
            status: form.status?.value,
            active_score: parseInt(form.active_score?.value || '0', 10),
            overall_score: parseFloat(form.overall_score?.value || '0'),
            weak_point: (form.weak_point?.value || '').trim() || null,
        };

        if (!payload.name) {
            setFormError('学生姓名不能为空');
            return;
        }

        setSubmitLoading(true);
        try {
            await request.put(API_ADMIN_UPDATE_STUDENT(editingStudent.id), payload);
            setEditingStudent(null);
            fetchData();
            toast.success('学生信息已更新');
        } catch (err) {
            setFormError(err.response?.data?.detail || err.message || '保存失败');
        } finally {
            setSubmitLoading(false);
        }
    };

    const handleDeleteStudent = async (id) => {
        if (!window.confirm('确认删除该学生账号？\n\n该操作不可恢复，请谨慎执行。')) return;
        try {
            await request.delete(API_ADMIN_DELETE_STUDENT(id));
            fetchData();
            toast.success('学生账号已删除');
        } catch (err) {
            setError(err.response?.data?.detail || err.message || '学生删除失败');
            toast.error(err.response?.data?.detail || err.message || '学生删除失败');
        }
    };

    const openResetPasswordModal = (account) => {
        setResettingAccount(account);
        setNewPassword('');
        setConfirmPassword('');
        setFormError('');
    };

    const handleResetPassword = async (e) => {
        e.preventDefault();
        if (!resettingAccount) return;

        if (!newPassword || !confirmPassword) {
            setFormError('请填写新密码并确认');
            return;
        }
        if (newPassword.length < 6) {
            setFormError('新密码长度不能小于 6 位');
            return;
        }
        if (newPassword !== confirmPassword) {
            setFormError('两次输入的新密码不一致');
            return;
        }

        setSubmitLoading(true);
        try {
            const newPasswordHash = await sha256Hex(newPassword);
            await request.put(API_ADMIN_RESET_USER_PASSWORD(resettingAccount.id), {
                new_password: newPasswordHash,
            });
            setResettingAccount(null);
            setNewPassword('');
            setConfirmPassword('');
            toast.success(`已重置 ${resettingAccount.name} 的密码`);
        } catch (err) {
            setFormError(err.response?.data?.detail || err.message || '重置密码失败');
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
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => fetchData(true)}
                            disabled={refreshing}
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/10 transition-colors disabled:opacity-60"
                        >
                            <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
                            刷新
                        </button>
                        <button
                            onClick={handleLogout}
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/10 transition-colors"
                        >
                            <LogOut size={18} />
                            退出登录
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 text-sm flex items-center justify-between gap-3">
                        <span>{error}</span>
                        <button type="button" onClick={() => setError('')} className="text-xs px-2 py-1 rounded border border-red-200 dark:border-red-700">关闭</button>
                    </div>
                )}

                <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div className="rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 p-3">
                        <p className="text-xs text-gray-500 dark:text-gray-400">教师总数</p>
                        <p className="text-xl font-semibold text-gray-900 dark:text-gray-100">{teachers.length}</p>
                    </div>
                    <div className="rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 p-3">
                        <p className="text-xs text-gray-500 dark:text-gray-400">可登录教师</p>
                        <p className="text-xl font-semibold text-emerald-600 dark:text-emerald-400">{activeTeacherCount}</p>
                    </div>
                    <div className="rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 p-3">
                        <p className="text-xs text-gray-500 dark:text-gray-400">班级总数</p>
                        <p className="text-xl font-semibold text-gray-900 dark:text-gray-100">{classes.length}</p>
                    </div>
                    <div className="rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 p-3">
                        <p className="text-xs text-gray-500 dark:text-gray-400">未分班学生</p>
                        <p className="text-xl font-semibold text-amber-600 dark:text-amber-400">{unassignedStudentCount}</p>
                    </div>
                </section>

                {/* 教师列表 */}
                <section className="rounded-2xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 overflow-hidden">
                    <div className="px-4 py-3 border-b border-gray-200 dark:border-white/10 flex items-center gap-2">
                        <Users className="text-indigo-500 dark:text-indigo-400" size={20} />
                        <h2 className="font-semibold text-gray-900 dark:text-gray-100">教师列表</h2>
                    </div>
                    <div className="px-4 pt-3 text-xs text-gray-500 dark:text-gray-400">
                        说明：登录权限用于控制教师是否可登录系统；审核状态用于注册审批流程。
                    </div>
                    <div className="p-4">
                        <div className="mb-3 relative max-w-md">
                            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                            <input
                                type="text"
                                value={teacherKeyword}
                                onChange={(e) => setTeacherKeyword(e.target.value)}
                                placeholder="搜索教师姓名、工号或 ID"
                                className="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                            />
                        </div>
                        {teachers.length === 0 ? (
                            <p className="text-sm text-gray-500 dark:text-gray-400">暂无教师账号</p>
                        ) : filteredTeachers.length === 0 ? (
                            <p className="text-sm text-gray-500 dark:text-gray-400">没有匹配的教师。</p>
                        ) : (
                            <ul className="space-y-2">
                                {filteredTeachers.map((t) => (
                                    <li key={t.id} className="flex flex-wrap items-center gap-2 py-2 px-3 rounded-lg bg-gray-50 dark:bg-white/5 text-sm">
                                        <span className="font-mono text-gray-500 dark:text-gray-400 w-20">ID {t.id}</span>
                                        <span className="font-medium text-gray-800 dark:text-gray-200">{t.display_name}</span>
                                        <span className="text-gray-500 dark:text-gray-400">({t.username})</span>
                                        <span className="text-xs px-2 py-0.5 rounded bg-indigo-50 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-300">负责班级: {t.class_count || 0}</span>
                                        <span className={`text-xs px-2 py-0.5 rounded ${t.status === 'approved' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300' : t.status === 'pending' ? 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300' : 'bg-rose-50 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300'}`}>
                                            {statusLabel(t.status)}
                                        </span>
                                        <select
                                            value={t.status || 'approved'}
                                            onChange={(e) => handleUpdateTeacher(t.id, { status: e.target.value })}
                                            className="ml-auto px-2 py-1 rounded border border-gray-200 dark:border-white/10 bg-white dark:bg-white/10 text-xs"
                                        >
                                            <option value="approved">审核通过</option>
                                            <option value="pending">待审核</option>
                                            <option value="rejected">已拒绝</option>
                                        </select>
                                        <button
                                            type="button"
                                            onClick={() => handleUpdateTeacher(t.id, { is_active: !t.is_active })}
                                            className={`px-2 py-1 rounded text-xs font-medium ${t.is_active ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'}`}
                                            title={t.is_active ? '当前允许该教师登录系统，点击后将停用登录权限' : '当前不允许该教师登录系统，点击后将恢复登录权限'}
                                        >
                                            {t.is_active ? '可登录' : '已停用登录'}
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => handleDeleteTeacher(t.id)}
                                            className="inline-flex items-center gap-1 px-2 py-1 rounded text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
                                        >
                                            <Trash2 size={12} /> 删除
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => openResetPasswordModal({ id: t.id, name: t.display_name || t.username, role: 'teacher' })}
                                            className="inline-flex items-center gap-1 px-2 py-1 rounded text-amber-700 hover:bg-amber-50 dark:text-amber-400 dark:hover:bg-amber-900/20"
                                        >
                                            <KeyRound size={12} /> 重置密码
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                </section>

                {/* 待审核教师 */}
                <section className="rounded-2xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 overflow-hidden">
                    <div className="px-4 py-3 border-b border-gray-200 dark:border-white/10 flex items-center gap-2">
                        <UserPlus className="text-amber-500 dark:text-amber-400" size={20} />
                        <h2 className="font-semibold text-gray-900 dark:text-gray-100 flex items-center">
                            待审核教师
                            {pendingTeachers.length > 0 && (
                                <span className="ml-2 bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">{pendingTeachers.length}</span>
                            )}
                        </h2>
                    </div>
                    <div className="p-4">
                        {pendingTeachers.length === 0 ? (
                            <p className="text-sm text-gray-500 dark:text-gray-400">暂无待审核申请</p>
                        ) : (
                            <ul className="space-y-2">
                                {pendingTeachers.map((t) => (
                                    <li key={t.id} className="flex flex-wrap flex-col sm:flex-row sm:items-center justify-between gap-3 py-3 px-4 rounded-xl bg-amber-50 dark:bg-amber-900/10 border border-amber-100 dark:border-amber-900/30 text-sm">
                                        <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                                            <span className="font-bold text-gray-800 dark:text-gray-200">{t.display_name}</span>
                                            <span className="text-gray-500 dark:text-gray-400">工号: {t.username}</span>
                                            <span className="text-gray-400 dark:text-gray-500 text-xs">申请时间: {new Date(t.created_at).toLocaleString()}</span>
                                        </div>
                                        <div className="flex gap-2">
                                            <button 
                                                onClick={() => handleApproveTeacher(t.id)}
                                                className="flex-1 sm:flex-none inline-flex items-center justify-center gap-1 px-3 py-1.5 rounded-lg bg-green-500 hover:bg-green-600 text-white font-medium transition-colors"
                                            >
                                                <CheckCircle size={14} /> 允许加入
                                            </button>
                                            <button 
                                                onClick={() => handleRejectTeacher(t.id)}
                                                className="flex-1 sm:flex-none inline-flex items-center justify-center gap-1 px-3 py-1.5 rounded-lg bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-500/20 font-medium transition-colors"
                                            >
                                                <XCircle size={14} /> 拒绝
                                            </button>
                                        </div>
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
                                        <span 
                                            className="font-mono text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 px-1.5 py-0.5 rounded cursor-pointer hover:bg-indigo-100 dark:hover:bg-indigo-900/50"
                                            title="点击复制邀请码"
                                            onClick={() => {
                                                navigator.clipboard.writeText(c.class_code);
                                                toast.success(`班级邀请码已复制：${c.class_code}`);
                                            }}
                                        >
                                            {c.class_code}
                                        </span>
                                        <span className="font-medium text-gray-800 dark:text-gray-200">{c.class_name}</span>
                                        {c.grade && <span className="text-gray-500 dark:text-gray-400">({c.grade})</span>}
                                        <span className="text-gray-500 dark:text-gray-400">— 负责教师: {c.teacher_display_name ?? c.teacher_username ?? `ID ${c.teacher_user_id}`}</span>
                                        <div className="ml-auto flex items-center gap-1">
                                            <button
                                                type="button"
                                                onClick={() => openEditModal(c)}
                                                className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 text-xs font-medium"
                                            >
                                                <Pencil size={12} />
                                                编辑
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => handleDeleteClass(c.id)}
                                                className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 text-xs font-medium"
                                            >
                                                <Trash2 size={12} />
                                                删除
                                            </button>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                </section>

                {/* 学生名单管理 */}
                <section className="rounded-2xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 overflow-hidden">
                    <div className="px-4 py-3 border-b border-gray-200 dark:border-white/10 flex items-center gap-2">
                        <Users className="text-teal-500 dark:text-teal-400" size={20} />
                        <h2 className="font-semibold text-gray-900 dark:text-gray-100">学生名单管理</h2>
                    </div>
                    <div className="p-4 overflow-x-auto">
                        <div className="mb-3 grid grid-cols-1 md:grid-cols-3 gap-2">
                            <div className="relative">
                                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                                <input
                                    type="text"
                                    value={studentKeyword}
                                    onChange={(e) => setStudentKeyword(e.target.value)}
                                    placeholder="搜索学号或姓名"
                                    className="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                                />
                            </div>
                            <select
                                value={studentStatusFilter}
                                onChange={(e) => setStudentStatusFilter(e.target.value)}
                                className="px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                            >
                                <option value="all">全部状态</option>
                                <option value="approved">审核通过</option>
                                <option value="pending">待审核</option>
                                <option value="rejected">已拒绝</option>
                            </select>
                            <select
                                value={classFilter}
                                onChange={(e) => setClassFilter(e.target.value)}
                                className="px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                            >
                                <option value="all">全部班级</option>
                                <option value="none">未分班</option>
                                {classes.map((c) => (
                                    <option key={c.id} value={String(c.id)}>{c.class_name}</option>
                                ))}
                            </select>
                        </div>
                        {students.length === 0 ? (
                            <p className="text-sm text-gray-500 dark:text-gray-400">暂无学生</p>
                        ) : (
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="text-left text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-white/10">
                                        <th className="py-2 pr-3">学号</th>
                                        <th className="py-2 pr-3">姓名</th>
                                        <th className="py-2 pr-3">班级</th>
                                        <th className="py-2 pr-3">状态</th>
                                        <th className="py-2 pr-3">活跃度</th>
                                        <th className="py-2 pr-3">综合分</th>
                                        <th className="py-2 text-right">操作</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredStudents.map((s) => (
                                        <tr key={s.id} className="border-b border-gray-100 dark:border-white/5">
                                            <td className="py-2 pr-3 font-mono">{s.uid}</td>
                                            <td className="py-2 pr-3">{s.name}</td>
                                            <td className="py-2 pr-3">{s.class_name || '未分班'}</td>
                                            <td className="py-2 pr-3">
                                                <span className={`text-xs px-2 py-0.5 rounded ${s.status === 'approved' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300' : s.status === 'pending' ? 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300' : 'bg-rose-50 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300'}`}>
                                                    {statusLabel(s.status)}
                                                </span>
                                            </td>
                                            <td className="py-2 pr-3">{Number(s.active_score ?? 0)}%</td>
                                            <td className="py-2 pr-3">{Number(s.overall_score ?? 0).toFixed(1)}</td>
                                            <td className="py-2 text-right space-x-2">
                                                <button
                                                    type="button"
                                                    onClick={() => openEditStudentModal(s)}
                                                    className="inline-flex items-center gap-1 px-2 py-1 rounded text-indigo-600 hover:bg-indigo-50 dark:text-indigo-400 dark:hover:bg-indigo-900/20"
                                                >
                                                    <Pencil size={12} /> 编辑
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={() => handleDeleteStudent(s.id)}
                                                    className="inline-flex items-center gap-1 px-2 py-1 rounded text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
                                                >
                                                    <Trash2 size={12} /> 删除
                                                </button>
                                                <button
                                                    type="button"
                                                    disabled={!s.user_id}
                                                    onClick={() => s.user_id && openResetPasswordModal({ id: s.user_id, name: s.name || s.uid, role: 'student' })}
                                                    className="inline-flex items-center gap-1 px-2 py-1 rounded text-amber-700 hover:bg-amber-50 dark:text-amber-400 dark:hover:bg-amber-900/20 disabled:opacity-50 disabled:cursor-not-allowed"
                                                >
                                                    <KeyRound size={12} /> 重置密码
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                        {students.length > 0 && filteredStudents.length === 0 && (
                            <p className="text-sm text-gray-500 dark:text-gray-400 py-3">没有符合筛选条件的学生。</p>
                        )}
                    </div>
                </section>

                {/* 系统设置 */}
                <section className="rounded-2xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 overflow-hidden">
                    <div className="px-4 py-3 border-b border-gray-200 dark:border-white/10 flex items-center gap-2">
                        <Settings className="text-gray-700 dark:text-gray-300" size={20} />
                        <h2 className="font-semibold text-gray-900 dark:text-gray-100">系统设置</h2>
                    </div>
                    <div className="p-4 space-y-4">
                        <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10">
                            <div>
                                <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">教师注册需要审核</h3>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">开启后，新注册的教师账号必须由管理员审核通过后才能登录使用。关闭则允许自由注册。</p>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer ml-4 shrink-0">
                                <input 
                                    type="checkbox" 
                                    className="sr-only peer" 
                                    checked={settings.REQUIRE_TEACHER_APPROVAL}
                                    onChange={(e) => toggleSetting('REQUIRE_TEACHER_APPROVAL', e.target.checked)}
                                />
                                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-indigo-300 dark:peer-focus:ring-indigo-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-indigo-600"></div>
                            </label>
                        </div>
                        <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10">
                            <div>
                                <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">学生注册需要审核</h3>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">开启后，填写班级邀请码注册的学生，需该班级负责教师点击审核通过后才能登录。未绑定班级的学生暂不受限或由管理员审核（视后续策略而定）。目前建议开启保障班级数据安全。</p>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer ml-4 shrink-0">
                                <input 
                                    type="checkbox" 
                                    className="sr-only peer" 
                                    checked={settings.REQUIRE_STUDENT_APPROVAL}
                                    onChange={(e) => toggleSetting('REQUIRE_STUDENT_APPROVAL', e.target.checked)}
                                />
                                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-indigo-300 dark:peer-focus:ring-indigo-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-indigo-600"></div>
                            </label>
                        </div>
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

            {/* 编辑学生弹窗 */}
            {editingStudent && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={() => !submitLoading && setEditingStudent(null)}>
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md p-6" onClick={e => e.stopPropagation()}>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">编辑学生 · {editingStudent.uid}</h3>
                        <form onSubmit={handleEditStudent}>
                            {formError && <p className="text-sm text-red-600 dark:text-red-400 mb-3">{formError}</p>}
                            <div className="space-y-3">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">姓名</label>
                                    <input name="name" type="text" required defaultValue={editingStudent.name} className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-sm" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">班级</label>
                                    <select name="class_id" defaultValue={editingStudent.class_id ?? ''} className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-sm">
                                        <option value="">未分班</option>
                                        {classes.map(c => <option key={c.id} value={c.id}>{c.class_name} ({c.class_code})</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">状态</label>
                                    <select name="status" defaultValue={editingStudent.status || 'approved'} className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-sm">
                                        <option value="approved">approved</option>
                                        <option value="pending">pending</option>
                                        <option value="rejected">rejected</option>
                                    </select>
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">活跃度</label>
                                        <input name="active_score" type="number" min="0" max="100" step="1" defaultValue={editingStudent.active_score ?? 0} className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-sm" />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">综合分</label>
                                        <input name="overall_score" type="number" min="0" max="100" step="0.1" defaultValue={editingStudent.overall_score ?? 0} className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-sm" />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">薄弱点（选填）</label>
                                    <input name="weak_point" type="text" defaultValue={editingStudent.weak_point ?? ''} className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-sm" />
                                </div>
                            </div>
                            <div className="flex gap-2 mt-6">
                                <button type="button" onClick={() => !submitLoading && setEditingStudent(null)} className="flex-1 py-2 rounded-lg border border-gray-200 dark:border-white/10 text-gray-700 dark:text-gray-300 text-sm font-medium">取消</button>
                                <button type="submit" disabled={submitLoading} className="flex-1 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium disabled:opacity-50">{submitLoading ? '保存中…' : '保存'}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* 重置账号密码弹窗 */}
            {resettingAccount && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={() => !submitLoading && setResettingAccount(null)}>
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md p-6" onClick={e => e.stopPropagation()}>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">重置账号密码</h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                            账号类型：{resettingAccount.role === 'teacher' ? '教师' : '学生'}，账号：{resettingAccount.name}
                        </p>
                        <form onSubmit={handleResetPassword}>
                            {formError && <p className="text-sm text-red-600 dark:text-red-400 mb-3">{formError}</p>}
                            <div className="space-y-3">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">新密码</label>
                                    <input
                                        type="password"
                                        value={newPassword}
                                        onChange={(e) => setNewPassword(e.target.value)}
                                        className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-sm"
                                        placeholder="至少 6 位"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">确认新密码</label>
                                    <input
                                        type="password"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-sm"
                                        placeholder="请再次输入新密码"
                                    />
                                </div>
                            </div>
                            <div className="flex gap-2 mt-6">
                                <button
                                    type="button"
                                    onClick={() => !submitLoading && setResettingAccount(null)}
                                    className="flex-1 py-2 rounded-lg border border-gray-200 dark:border-white/10 text-gray-700 dark:text-gray-300 text-sm font-medium"
                                >
                                    取消
                                </button>
                                <button
                                    type="submit"
                                    disabled={submitLoading}
                                    className="flex-1 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-sm font-medium disabled:opacity-50"
                                >
                                    {submitLoading ? '提交中…' : '确认重置'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminDashboard;
