import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import request from '../../api/request';
import { LogOut, Users, BookOpen, Loader2, Shield, Plus, Pencil, Settings, UserPlus, Trash2, CheckCircle, XCircle, Search, RefreshCw, KeyRound, Database, Upload } from 'lucide-react';
import { useToast } from '../../components/Toast';
import { sha256Hex } from '../../utils/security';
import { parseStoredUserInfo } from '../../utils/safeJson';
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
    API_ADMIN_KB_DOCS,
    API_ADMIN_KB_UPLOAD,
    API_ADMIN_KB_REINDEX,
    API_ADMIN_KB_DELETE_DOC,
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
    const [showEditTeacherModal, setShowEditTeacherModal] = useState(false);
    const [editingTeacher, setEditingTeacher] = useState(null);
    const [submitLoading, setSubmitLoading] = useState(false);
    const [formError, setFormError] = useState('');
    const [refreshing, setRefreshing] = useState(false);
    const [resettingAccount, setResettingAccount] = useState(null);
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [teacherKeyword, setTeacherKeyword] = useState('');
    const [studentKeyword, setStudentKeyword] = useState('');
    const [isPendingPanelOpen, setIsPendingPanelOpen] = useState(false);
    const [createTeacherKeyword, setCreateTeacherKeyword] = useState('');
    const [editClassTeacherKeyword, setEditClassTeacherKeyword] = useState('');
    const [createClassTeacherIds, setCreateClassTeacherIds] = useState([]);
    const [editClassTeacherIds, setEditClassTeacherIds] = useState([]);
    const [editTeacherClassKeyword, setEditTeacherClassKeyword] = useState('');
    const [editTeacherClassIds, setEditTeacherClassIds] = useState([]);
    const [kbDocs, setKbDocs] = useState([]);
    const [kbUploading, setKbUploading] = useState(false);
    const [kbReindexingId, setKbReindexingId] = useState(null);
    const [kbDeletingId, setKbDeletingId] = useState(null);
    const [kbError, setKbError] = useState('');

    const userInfo = parseStoredUserInfo();
    const adminName = userInfo.name || '管理员';
    const activeTeacherCount = teachers.filter((t) => t.is_active).length;
    const unassignedStudentCount = students.filter((s) => {
        const classIds = Array.isArray(s.class_ids)
            ? s.class_ids.filter((id) => Number.isInteger(parseInt(id, 10)))
            : [];
        return classIds.length === 0 && (s.class_id == null);
    }).length;
    const unassignedTeacherCount = teachers.filter((t) => t.class_count === 0).length;

    const statusLabel = (status) => {
        if (status === 'approved') return '审核通过';
        if (status === 'pending') return '待审核';
        if (status === 'rejected') return '已拒绝';
        return status || '未知';
    };

    const normalizeTeacherIds = useCallback((classroom) => {
        if (!classroom) return [];
        if (Array.isArray(classroom.teacher_user_ids)) {
            return classroom.teacher_user_ids
                .map((id) => parseInt(id, 10))
                .filter((id) => Number.isInteger(id));
        }
        if (classroom.teacher_user_id != null) {
            const id = parseInt(classroom.teacher_user_id, 10);
            return Number.isInteger(id) ? [id] : [];
        }
        return [];
    }, []);

    const filteredCreateTeachers = useMemo(() => {
        const keyword = createTeacherKeyword.trim().toLowerCase();
        if (!keyword) return teachers;
        return teachers.filter((t) =>
            String(t.display_name || '').toLowerCase().includes(keyword) ||
            String(t.username || '').toLowerCase().includes(keyword)
        );
    }, [teachers, createTeacherKeyword]);

    const filteredEditClassTeachers = useMemo(() => {
        const keyword = editClassTeacherKeyword.trim().toLowerCase();
        if (!keyword) return teachers;
        return teachers.filter((t) =>
            String(t.display_name || '').toLowerCase().includes(keyword) ||
            String(t.username || '').toLowerCase().includes(keyword)
        );
    }, [teachers, editClassTeacherKeyword]);

    const filteredEditTeacherClasses = useMemo(() => {
        const keyword = editTeacherClassKeyword.trim().toLowerCase();
        if (!keyword) return classes;
        return classes.filter((c) =>
            String(c.class_name || '').toLowerCase().includes(keyword) ||
            String(c.class_code || '').toLowerCase().includes(keyword)
        );
    }, [classes, editTeacherClassKeyword]);

    const getStudentClassIds = useCallback((student) => {
        if (Array.isArray(student?.class_ids) && student.class_ids.length > 0) {
            return student.class_ids
                .map((id) => parseInt(id, 10))
                .filter((id) => Number.isInteger(id));
        }
        if (student?.class_id != null) {
            const id = parseInt(student.class_id, 10);
            return Number.isInteger(id) ? [id] : [];
        }
        return [];
    }, []);

    const classUnits = useMemo(() => {
        const teacherMap = new Map(teachers.map((t) => [t.id, t]));
        const studentMap = new Map();

        students.forEach((s) => {
            const classIds = getStudentClassIds(s);
            classIds.forEach((classId) => {
                const key = String(classId);
                const arr = studentMap.get(key) || [];
                arr.push(s);
                studentMap.set(key, arr);
            });
        });

        const byClass = classes.map((c) => {
            const teacherIds = normalizeTeacherIds(c);
            const classTeachers = teacherIds
                .map((id) => teacherMap.get(id))
                .filter(Boolean);
            return {
                classId: c.id,
                classCode: c.class_code,
                className: c.class_name,
                grade: c.grade,
                teachers: classTeachers,
                students: studentMap.get(String(c.id)) || [],
                classInfo: c,
            };
        });

        const classKeyword = teacherKeyword.trim().toLowerCase();
        const stuKeyword = studentKeyword.trim().toLowerCase();

        return byClass.filter((unit) => {
            const hitClass = !classKeyword ||
                String(unit.className || '').toLowerCase().includes(classKeyword) ||
                String(unit.classCode || '').toLowerCase().includes(classKeyword) ||
                unit.teachers.some((teacher) =>
                    String(teacher.display_name || '').toLowerCase().includes(classKeyword) ||
                    String(teacher.username || '').toLowerCase().includes(classKeyword)
                );

            const hitStudents = !stuKeyword || unit.students.some((s) =>
                String(s.name || '').toLowerCase().includes(stuKeyword) ||
                String(s.uid || '').toLowerCase().includes(stuKeyword)
            );

            return hitClass && hitStudents;
        });
    }, [classes, teachers, students, teacherKeyword, studentKeyword, normalizeTeacherIds, getStudentClassIds]);

    const filteredUnassignedStudents = useMemo(() => {
        const classKeyword = teacherKeyword.trim().toLowerCase();
        const stuKeyword = studentKeyword.trim().toLowerCase();
        return students
            .filter((s) => getStudentClassIds(s).length === 0)
            .filter((s) => {
                const target = `${s.name || ''} ${s.uid || ''}`.toLowerCase();
                const hitClass = !classKeyword || '未分班学生'.includes(classKeyword) || target.includes(classKeyword);
                const hitStudent = !stuKeyword || target.includes(stuKeyword);
                return hitClass && hitStudent;
            });
    }, [students, teacherKeyword, studentKeyword, getStudentClassIds]);

    const filteredUnassignedTeachers = useMemo(() => {
        const classKeyword = teacherKeyword.trim().toLowerCase();
        return teachers
            .filter((t) => t.class_count === 0)
            .filter((t) => {
                const target = `${t.display_name || ''} ${t.username || ''}`.toLowerCase();
                return !classKeyword || '未分班教师'.includes(classKeyword) || target.includes(classKeyword);
            });
    }, [teachers, teacherKeyword]);

    const fetchData = useCallback(async (showToast = false) => {
        setError('');
        if (showToast) setRefreshing(true);
        try {
            const [teachersRes, classesRes, settingsRes, pendingRes, studentsRes, kbRes] = await Promise.all([
                request.get(API_ADMIN_TEACHERS),
                request.get(API_ADMIN_CLASSES),
                request.get(API_ADMIN_SETTINGS),
                request.get(API_ADMIN_PENDING_TEACHERS),
                request.get(API_ADMIN_STUDENTS),
                request.get(API_ADMIN_KB_DOCS),
            ]);
            setTeachers(Array.isArray(teachersRes.data) ? teachersRes.data : []);
            setClasses(Array.isArray(classesRes.data) ? classesRes.data : []);
            setSettings(settingsRes.data || { REQUIRE_TEACHER_APPROVAL: false, REQUIRE_STUDENT_APPROVAL: false });
            setPendingTeachers(Array.isArray(pendingRes.data) ? pendingRes.data : []);
            setStudents(Array.isArray(studentsRes.data) ? studentsRes.data : []);
            setKbDocs(Array.isArray(kbRes.data) ? kbRes.data : []);
            if (showToast) toast.success('数据已刷新');
        } catch (err) {
            console.error('管理员数据加载失败:', err);
            setError(err.response?.data?.detail || err.message || '加载失败');
            setTeachers([]);
            setClasses([]);
            setPendingTeachers([]);
            setStudents([]);
            setKbDocs([]);
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
        const teacher_user_ids = [...new Set(createClassTeacherIds)]
            .map((id) => parseInt(id, 10))
            .filter((v) => Number.isInteger(v));
        setFormError('');
        if (!class_code || !class_name || teacher_user_ids.length === 0) {
            setFormError('请填写班级代码、班级名称并选择至少一名负责教师');
            return;
        }
        setSubmitLoading(true);
        try {
            await request.post(API_ADMIN_CLASSES, { class_code, class_name, grade, teacher_user_ids });
            setShowCreateModal(false);
            form.reset();
            setCreateClassTeacherIds([]);
            setCreateTeacherKeyword('');
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
        setEditClassTeacherIds(normalizeTeacherIds(c));
        setEditClassTeacherKeyword('');
        setFormError('');
        setShowEditModal(true);
    };

    const handleEditClass = async (e) => {
        e.preventDefault();
        if (!editingClass) return;
        const form = e.target;
        const class_name = (form.class_name?.value || '').trim();
        const grade = (form.grade?.value || '').trim() || null;
        const teacher_user_ids = [...new Set(editClassTeacherIds)]
            .map((id) => parseInt(id, 10))
            .filter((v) => Number.isInteger(v));
        setFormError('');
        if (!class_name) {
            setFormError('请填写班级名称');
            return;
        }
        if (teacher_user_ids.length === 0) {
            setFormError('请至少选择一名负责教师');
            return;
        }
        setSubmitLoading(true);
        try {
            await request.put(`${API_ADMIN_CLASSES}/${editingClass.id}`, {
                class_name,
                grade: grade || undefined,
                teacher_user_ids,
            });
            setShowEditModal(false);
            setEditingClass(null);
            setEditClassTeacherIds([]);
            setEditClassTeacherKeyword('');
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

    const openEditTeacherModal = (teacher) => {
        setEditingTeacher(teacher);
        const initialClassIds = classes
            .filter((c) => normalizeTeacherIds(c).includes(teacher.id))
            .map((c) => c.id);
        setEditTeacherClassIds(initialClassIds);
        setEditTeacherClassKeyword('');
        setFormError('');
        setShowEditTeacherModal(true);
    };

    const handleEditTeacher = async (e) => {
        e.preventDefault();
        if (!editingTeacher) return;
        const form = e.target;
        const display_name = (form.display_name?.value || '').trim();
        const class_ids = [...new Set(editTeacherClassIds)]
            .map((id) => parseInt(id, 10))
            .filter((v) => Number.isInteger(v));
        setFormError('');
        if (!display_name) {
            setFormError('教师姓名不能为空');
            return;
        }
        setSubmitLoading(true);
        try {
            const payload = { display_name, class_ids };
            await request.put(API_ADMIN_UPDATE_TEACHER(editingTeacher.id), payload);
            setShowEditTeacherModal(false);
            setEditingTeacher(null);
            setEditTeacherClassIds([]);
            setEditTeacherClassKeyword('');
            fetchData();
            toast.success('教师信息已更新');
        } catch (err) {
            setFormError(err.response?.data?.detail || err.message || '保存失败');
        } finally {
            setSubmitLoading(false);
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

    const handleUpdateStudentQuick = async (id, payload) => {
        try {
            await request.put(API_ADMIN_UPDATE_STUDENT(id), payload);
            fetchData();
            toast.success('学生信息已更新');
        } catch (err) {
            setError(err.response?.data?.detail || err.message || '学生信息更新失败');
            toast.error(err.response?.data?.detail || err.message || '学生信息更新失败');
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

    const handleKbUpload = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const fd = new FormData();
        fd.append('file', file);
        setKbError('');
        setKbUploading(true);
        try {
            // 解析 PDF + 批量调用 DashScope embedding，常超过全局 axios 15s，需单独加长超时
            await request.post(API_ADMIN_KB_UPLOAD, fd, {
                headers: { 'Content-Type': 'multipart/form-data' },
                timeout: 600000,
            });
            await fetchData();
            toast.success('上传并索引完成');
        } catch (err) {
            setKbError(err.response?.data?.detail || err.message || '上传失败');
        } finally {
            setKbUploading(false);
            e.target.value = '';
        }
    };

    const handleKbReindex = async (docId) => {
        setKbError('');
        setKbReindexingId(docId);
        try {
            await request.post(`${API_ADMIN_KB_REINDEX}/${docId}`, {}, {
                timeout: 600000,
            });
            await fetchData();
            toast.success('重建索引完成');
        } catch (err) {
            setKbError(err.response?.data?.detail || err.message || '重建失败');
        } finally {
            setKbReindexingId(null);
        }
    };

    const handleKbDelete = async (docId, title) => {
        if (!window.confirm(`确定删除「${title || '该文档'}」？将同时从向量库与服务器文件中移除，且无法恢复。`)) {
            return;
        }
        setKbError('');
        setKbDeletingId(docId);
        try {
            await request.delete(API_ADMIN_KB_DELETE_DOC(docId), { timeout: 60000 });
            await fetchData();
            toast.success('已删除文档');
        } catch (err) {
            setKbError(err.response?.data?.detail || err.message || '删除失败');
        } finally {
            setKbDeletingId(null);
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
        <div className="teacher-shell p-3 sm:p-4 md:p-8">
            <div className="max-w-6xl mx-auto space-y-5 md:space-y-6">
                {/* 页面标题区 */}
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 sm:gap-4">
                    <div>
                        <h1 className="text-xl sm:text-2xl md:text-3xl teacher-section-title flex items-center gap-2 sm:gap-3">
                            <Shield className="text-amber-500 dark:text-amber-400 shrink-0" />
                            管理员工作台
                        </h1>
                        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1.5">欢迎，{adminName}。请先处理待审核，再进行班级和账号维护。</p>
                    </div>
                    <div className="teacher-panel rounded-2xl px-3 sm:px-4 py-3 flex flex-col gap-2.5 w-full sm:w-auto shrink-0">
                        <div className="flex items-center gap-3">
                            <div className="h-11 w-11 rounded-full bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 font-bold flex items-center justify-center">
                                {(adminName || '管')[0]}
                            </div>
                            <div className="min-w-0">
                                <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 truncate max-w-[160px]">{adminName}</p>
                                <p className="text-xs text-slate-500 dark:text-slate-400">管理员账号</p>
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            <button
                                type="button"
                                onClick={() => fetchData(true)}
                                disabled={refreshing}
                                className="teacher-action-secondary h-9 px-3 rounded-xl text-xs sm:text-sm font-medium flex items-center justify-center gap-1.5 disabled:opacity-60"
                            >
                                <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} /> 刷新
                            </button>
                            <button
                                type="button"
                                onClick={handleLogout}
                                className="h-9 px-3 rounded-xl text-xs sm:text-sm font-medium flex items-center justify-center gap-1.5 bg-red-50 dark:bg-red-900/25 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800/40 hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors"
                            >
                                <LogOut size={14} /> 退出
                            </button>
                        </div>
                    </div>
                </div>

                {/* 管理操作区 */}
                <div className="teacher-panel rounded-2xl p-3 sm:p-4 md:p-5">
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
                        <div className="rounded-xl border border-slate-200/80 dark:border-slate-700/80 p-3 bg-white/50 dark:bg-slate-900/50">
                            <p className="text-xs font-semibold tracking-wide text-slate-500 dark:text-slate-400 mb-2">日常管理</p>
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                <button
                                    type="button"
                                    onClick={() => {
                                        setCreateClassTeacherIds([]);
                                        setCreateTeacherKeyword('');
                                        setShowCreateModal(true);
                                        setFormError('');
                                    }}
                                    className="teacher-action-primary h-10 px-3 rounded-xl font-medium text-sm flex items-center justify-center gap-1.5"
                                >
                                    <Plus size={16} /> 新建班级
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setIsPendingPanelOpen(true)}
                                    className="teacher-action-secondary h-10 px-3 rounded-xl font-medium text-sm flex items-center justify-center gap-1.5"
                                >
                                    <UserPlus size={16} /> 审核教师
                                    {pendingTeachers.length > 0 && (
                                        <span className="inline-flex items-center justify-center min-w-5 h-5 px-1 rounded-full bg-red-500 text-white text-xs font-bold">
                                            {pendingTeachers.length}
                                        </span>
                                    )}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => {
                                        setTeacherKeyword('');
                                        setStudentKeyword('');
                                    }}
                                    className="teacher-action-secondary h-10 px-3 rounded-xl font-medium text-sm flex items-center justify-center gap-1.5"
                                >
                                    <Search size={16} /> 清空筛选
                                </button>
                            </div>
                        </div>
                        <div className="rounded-xl border border-slate-200/80 dark:border-slate-700/80 p-3 bg-white/50 dark:bg-slate-900/50">
                            <p className="text-xs font-semibold tracking-wide text-slate-500 dark:text-slate-400 mb-2">状态总览</p>
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                                <div className="rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/40 px-2.5 py-2">
                                    <p className="text-amber-700 dark:text-amber-300">待审核教师</p>
                                    <p className="text-base font-bold text-amber-700 dark:text-amber-300">{pendingTeachers.length}</p>
                                </div>
                                <div className="rounded-lg bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800/40 px-2.5 py-2">
                                    <p className="text-emerald-700 dark:text-emerald-300">可登录教师</p>
                                    <p className="text-base font-bold text-emerald-700 dark:text-emerald-300">{activeTeacherCount}</p>
                                </div>
                                <div className="rounded-lg bg-sky-50 dark:bg-sky-900/20 border border-sky-200 dark:border-sky-800/40 px-2.5 py-2">
                                    <p className="text-sky-700 dark:text-sky-300">班级总数</p>
                                    <p className="text-base font-bold text-sky-700 dark:text-sky-300">{classes.length}</p>
                                </div>
                                <div className="rounded-lg bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800/40 px-2.5 py-2">
                                    <p className="text-rose-700 dark:text-rose-300">未分班学生</p>
                                    <p className="text-base font-bold text-rose-700 dark:text-rose-300">{unassignedStudentCount}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {error && (
                    <div className="rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 text-sm flex items-center justify-between gap-3">
                        <span>{error}</span>
                        <button type="button" onClick={() => setError('')} className="text-xs px-2 py-1 rounded border border-red-200 dark:border-red-700">关闭</button>
                    </div>
                )}

                <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div className="teacher-panel rounded-xl border border-slate-200/80 dark:border-slate-700/80 p-3">
                        <p className="text-xs text-gray-500 dark:text-gray-400">教师总数</p>
                        <p className="text-xl font-semibold text-gray-900 dark:text-gray-100">{teachers.length}</p>
                    </div>
                    <div className="teacher-panel rounded-xl border border-slate-200/80 dark:border-slate-700/80 p-3">
                        <p className="text-xs text-gray-500 dark:text-gray-400">可登录教师</p>
                        <p className="text-xl font-semibold text-emerald-600 dark:text-emerald-400">{activeTeacherCount}</p>
                    </div>
                    <div className="teacher-panel rounded-xl border border-slate-200/80 dark:border-slate-700/80 p-3">
                        <p className="text-xs text-gray-500 dark:text-gray-400">班级总数</p>
                        <p className="text-xl font-semibold text-gray-900 dark:text-gray-100">{classes.length}</p>
                    </div>
                    <div className="teacher-panel rounded-xl border border-slate-200/80 dark:border-slate-700/80 p-3">
                        <p className="text-xs text-gray-500 dark:text-gray-400">未分班学生</p>
                        <p className="text-xl font-semibold text-amber-600 dark:text-amber-400">{unassignedStudentCount}</p>
                    </div>
                    <div className="teacher-panel rounded-xl border border-slate-200/80 dark:border-slate-700/80 p-3">
                        <p className="text-xs text-gray-500 dark:text-gray-400">未分班教师</p>
                        <p className="text-xl font-semibold text-violet-600 dark:text-violet-400">{unassignedTeacherCount}</p>
                    </div>
                </section>

                {/* 统一按班级管理 */}
                <section className="teacher-panel rounded-2xl border border-slate-200/80 dark:border-slate-700/80 overflow-hidden">
                    <div className="px-4 py-3 border-b border-gray-200 dark:border-white/10 flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                        <div className="flex items-center gap-2">
                            <BookOpen className="text-indigo-500 dark:text-indigo-400" size={20} />
                            <h2 className="font-semibold text-gray-900 dark:text-gray-100">按班级统一管理</h2>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full md:w-auto">
                            <div className="relative">
                                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                                <input
                                    type="text"
                                    value={teacherKeyword}
                                    onChange={(e) => setTeacherKeyword(e.target.value)}
                                    placeholder="筛选班级/教师"
                                    className="w-full md:w-56 pl-9 pr-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                                />
                            </div>
                            <div className="relative">
                                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                                <input
                                    type="text"
                                    value={studentKeyword}
                                    onChange={(e) => setStudentKeyword(e.target.value)}
                                    placeholder="筛选学生"
                                    className="w-full md:w-56 pl-9 pr-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                                />
                            </div>
                        </div>
                    </div>
                    <div className="p-4 space-y-4">
                        {classUnits.length === 0 ? (
                            <p className="text-sm text-gray-500 dark:text-gray-400">当前没有匹配的班级单元。</p>
                        ) : (
                            classUnits.map((unit) => (
                                <article key={String(unit.classId)} className="rounded-2xl border border-slate-200/80 dark:border-slate-700/70 bg-white/60 dark:bg-slate-900/40 p-3 sm:p-4 space-y-3">
                                    <div className="flex flex-wrap items-center justify-between gap-2">
                                        <div className="flex items-center gap-2 flex-wrap">
                                            <span className="font-mono text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 px-2 py-1 rounded text-xs">{unit.classCode}</span>
                                            <span className="font-semibold text-slate-800 dark:text-slate-100">{unit.className}</span>
                                            {unit.grade && <span className="text-xs text-slate-500 dark:text-slate-400">({unit.grade})</span>}
                                        </div>
                                        {unit.classInfo && (
                                            <div className="flex items-center gap-1">
                                                <button type="button" onClick={() => openEditModal(unit.classInfo)} className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 text-xs font-medium">
                                                    <Pencil size={12} /> 编辑班级
                                                </button>
                                                <button type="button" onClick={() => handleDeleteClass(unit.classInfo.id)} className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 text-xs font-medium">
                                                    <Trash2 size={12} /> 删除班级
                                                </button>
                                            </div>
                                        )}
                                    </div>

                                    {unit.classInfo && (
                                        <div className="rounded-xl border border-sky-200/70 dark:border-sky-800/50 bg-sky-50/60 dark:bg-sky-900/10 p-3">
                                            <p className="text-xs font-semibold text-sky-700 dark:text-sky-300 mb-2">教师模块</p>
                                            {unit.teachers.length > 0 ? (
                                                <div className="space-y-2">
                                                    {unit.teachers.map((teacher) => (
                                                        <div key={teacher.id} className="flex flex-wrap items-center gap-2 text-sm rounded-lg border border-sky-200/70 dark:border-sky-800/60 bg-white/70 dark:bg-slate-900/30 px-2.5 py-2">
                                                            <span className="font-medium text-slate-800 dark:text-slate-100">{teacher.display_name}</span>
                                                            <span className="text-slate-500 dark:text-slate-400">({teacher.username})</span>
                                                            <select
                                                                value={teacher.status || 'approved'}
                                                                onChange={(e) => handleUpdateTeacher(teacher.id, { status: e.target.value })}
                                                                className="px-2 py-1 rounded border border-gray-200 dark:border-white/10 bg-white dark:bg-white/10 text-xs"
                                                            >
                                                                <option value="approved">审核通过</option>
                                                                <option value="pending">待审核</option>
                                                                <option value="rejected">已拒绝</option>
                                                            </select>
                                                            <button
                                                                type="button"
                                                                onClick={() => handleUpdateTeacher(teacher.id, { is_active: !teacher.is_active })}
                                                                className={`px-2 py-1 rounded text-xs font-medium ${teacher.is_active ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'}`}
                                                            >
                                                                {teacher.is_active ? '可登录' : '已停用登录'}
                                                            </button>
                                                            <button type="button" onClick={() => openEditTeacherModal(teacher)} className="inline-flex items-center gap-1 px-2 py-1 rounded text-indigo-600 hover:bg-indigo-50 dark:text-indigo-400 dark:hover:bg-indigo-900/20 text-xs">
                                                                <Pencil size={12} /> 编辑
                                                            </button>
                                                            <button type="button" onClick={() => openResetPasswordModal({ id: teacher.id, name: teacher.display_name || teacher.username, role: 'teacher' })} className="inline-flex items-center gap-1 px-2 py-1 rounded text-amber-700 hover:bg-amber-50 dark:text-amber-400 dark:hover:bg-amber-900/20 text-xs">
                                                                <KeyRound size={12} /> 重置密码
                                                            </button>
                                                            <button type="button" onClick={() => handleDeleteTeacher(teacher.id)} className="inline-flex items-center gap-1 px-2 py-1 rounded text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20 text-xs">
                                                                <Trash2 size={12} /> 删除教师
                                                            </button>
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <p className="text-sm text-slate-500 dark:text-slate-400">该班级暂未分配教师。</p>
                                            )}
                                        </div>
                                    )}

                                    <div className="rounded-xl border border-teal-200/70 dark:border-teal-800/50 bg-teal-50/60 dark:bg-teal-900/10 p-3">
                                        <p className="text-xs font-semibold text-teal-700 dark:text-teal-300 mb-2">学生模块</p>
                                        {unit.students.length === 0 ? (
                                            <p className="text-sm text-slate-500 dark:text-slate-400">暂无学生。</p>
                                        ) : (
                                            <ul className="space-y-2">
                                                {unit.students.map((s) => (
                                                    <li key={s.id} className="flex flex-wrap items-center gap-2 py-2 px-3 rounded-lg bg-white/70 dark:bg-slate-900/45 text-sm">
                                                        <span className="font-mono text-slate-500 dark:text-slate-400">{s.uid}</span>
                                                        <span className="font-medium text-slate-800 dark:text-slate-100">{s.name}</span>
                                                        <select
                                                            value={s.status || 'approved'}
                                                            onChange={(e) => handleUpdateStudentQuick(s.id, { status: e.target.value })}
                                                            className="px-2 py-1 rounded border border-gray-200 dark:border-white/10 bg-white dark:bg-white/10 text-xs"
                                                        >
                                                            <option value="approved">审核通过</option>
                                                            <option value="pending">待审核</option>
                                                            <option value="rejected">已拒绝</option>
                                                        </select>
                                                        <button
                                                            type="button"
                                                            onClick={() => handleUpdateStudentQuick(s.id, { is_active: !s.is_active })}
                                                            className={`px-2 py-1 rounded text-xs font-medium ${s.is_active ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'}`}
                                                        >
                                                            {s.is_active ? '可登录' : '已停用登录'}
                                                        </button>
                                                        <button type="button" onClick={() => openEditStudentModal(s)} className="inline-flex items-center gap-1 px-2 py-1 rounded text-indigo-600 hover:bg-indigo-50 dark:text-indigo-400 dark:hover:bg-indigo-900/20 text-xs">
                                                            <Pencil size={12} /> 编辑
                                                        </button>
                                                        <button type="button" disabled={!s.user_id} onClick={() => s.user_id && openResetPasswordModal({ id: s.user_id, name: s.name || s.uid, role: 'student' })} className="inline-flex items-center gap-1 px-2 py-1 rounded text-amber-700 hover:bg-amber-50 dark:text-amber-400 dark:hover:bg-amber-900/20 text-xs disabled:opacity-50 disabled:cursor-not-allowed">
                                                            <KeyRound size={12} /> 重置密码
                                                        </button>
                                                        <button type="button" onClick={() => handleDeleteStudent(s.id)} className="inline-flex items-center gap-1 px-2 py-1 rounded text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20 text-xs">
                                                            <Trash2 size={12} /> 删除
                                                        </button>
                                                    </li>
                                                ))}
                                            </ul>
                                        )}
                                    </div>
                                </article>
                            ))
                        )}
                        
                    </div>
                </section>

                {/* 未分班管理 */}
                <section className="teacher-panel rounded-2xl border border-slate-200/80 dark:border-slate-700/80 overflow-hidden">
                    <div className="px-4 py-3 border-b border-gray-200 dark:border-white/10 flex items-center gap-2">
                        <Users className="text-violet-500 dark:text-violet-400" size={20} />
                        <h2 className="font-semibold text-gray-900 dark:text-gray-100">未分班管理</h2>
                    </div>
                    <div className="p-4 grid grid-cols-1 xl:grid-cols-2 gap-4">
                        <article className="rounded-2xl border border-amber-200/80 dark:border-amber-700/70 bg-amber-50/60 dark:bg-amber-900/12 p-3 sm:p-4 space-y-3">
                            <div className="flex items-center justify-between gap-2">
                                <h3 className="font-semibold text-amber-700 dark:text-amber-300">未分班学生</h3>
                                <span className="text-xs text-amber-700/90 dark:text-amber-300/90">{filteredUnassignedStudents.length} 人</span>
                            </div>
                            {filteredUnassignedStudents.length === 0 ? (
                                <p className="text-sm text-slate-500 dark:text-slate-400">没有匹配的未分班学生。</p>
                            ) : (
                                <ul className="space-y-2">
                                    {filteredUnassignedStudents.map((s) => (
                                        <li key={s.id} className="flex flex-wrap items-center gap-2 py-2 px-3 rounded-lg bg-white/70 dark:bg-slate-900/45 text-sm">
                                            <span className="font-mono text-slate-500 dark:text-slate-400">{s.uid}</span>
                                            <span className="font-medium text-slate-800 dark:text-slate-100">{s.name}</span>
                                            <select
                                                value={s.status || 'approved'}
                                                onChange={(e) => handleUpdateStudentQuick(s.id, { status: e.target.value })}
                                                className="px-2 py-1 rounded border border-gray-200 dark:border-white/10 bg-white dark:bg-white/10 text-xs"
                                            >
                                                <option value="approved">审核通过</option>
                                                <option value="pending">待审核</option>
                                                <option value="rejected">已拒绝</option>
                                            </select>
                                            <button
                                                type="button"
                                                onClick={() => handleUpdateStudentQuick(s.id, { is_active: !s.is_active })}
                                                className={`px-2 py-1 rounded text-xs font-medium ${s.is_active ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'}`}
                                            >
                                                {s.is_active ? '可登录' : '已停用登录'}
                                            </button>
                                            <button type="button" onClick={() => openEditStudentModal(s)} className="inline-flex items-center gap-1 px-2 py-1 rounded text-indigo-600 hover:bg-indigo-50 dark:text-indigo-400 dark:hover:bg-indigo-900/20 text-xs">
                                                <Pencil size={12} /> 编辑
                                            </button>
                                            <button type="button" disabled={!s.user_id} onClick={() => s.user_id && openResetPasswordModal({ id: s.user_id, name: s.name || s.uid, role: 'student' })} className="inline-flex items-center gap-1 px-2 py-1 rounded text-amber-700 hover:bg-amber-50 dark:text-amber-400 dark:hover:bg-amber-900/20 text-xs disabled:opacity-50 disabled:cursor-not-allowed">
                                                <KeyRound size={12} /> 重置密码
                                            </button>
                                            <button type="button" onClick={() => handleDeleteStudent(s.id)} className="inline-flex items-center gap-1 px-2 py-1 rounded text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20 text-xs">
                                                <Trash2 size={12} /> 删除
                                            </button>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </article>

                        <article className="rounded-2xl border border-violet-200/80 dark:border-violet-700/70 bg-violet-50/60 dark:bg-violet-900/20 p-3 sm:p-4 space-y-3">
                            <div className="flex items-center justify-between gap-2">
                                <h3 className="font-semibold text-violet-700 dark:text-violet-300">未分班教师</h3>
                                <span className="text-xs text-violet-700/90 dark:text-violet-300/90">{filteredUnassignedTeachers.length} 人</span>
                            </div>
                            {filteredUnassignedTeachers.length === 0 ? (
                                <p className="text-sm text-slate-500 dark:text-slate-400">没有匹配的未分班教师。</p>
                            ) : (
                                <ul className="space-y-2">
                                    {filteredUnassignedTeachers.map((t) => (
                                        <li key={t.id} className="flex flex-wrap items-center gap-2 py-2 px-3 rounded-lg bg-white/70 dark:bg-slate-900/45 text-sm">
                                            <span className="font-medium text-slate-800 dark:text-slate-100">{t.display_name}</span>
                                            <span className="text-slate-500 dark:text-slate-400">({t.username})</span>
                                            <select
                                                value={t.status || 'approved'}
                                                onChange={(e) => handleUpdateTeacher(t.id, { status: e.target.value })}
                                                className="px-2 py-1 rounded border border-gray-200 dark:border-white/10 bg-white dark:bg-white/10 text-xs"
                                            >
                                                <option value="approved">审核通过</option>
                                                <option value="pending">待审核</option>
                                                <option value="rejected">已拒绝</option>
                                            </select>
                                            <button
                                                type="button"
                                                onClick={() => handleUpdateTeacher(t.id, { is_active: !t.is_active })}
                                                className={`px-2 py-1 rounded text-xs font-medium ${t.is_active ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'}`}
                                            >
                                                {t.is_active ? '可登录' : '已停用登录'}
                                            </button>
                                            <button type="button" onClick={() => openEditTeacherModal(t)} className="inline-flex items-center gap-1 px-2 py-1 rounded text-indigo-600 hover:bg-indigo-50 dark:text-indigo-400 dark:hover:bg-indigo-900/20 text-xs">
                                                <Pencil size={12} /> 编辑
                                            </button>
                                            <button type="button" onClick={() => openResetPasswordModal({ id: t.id, name: t.display_name || t.username, role: 'teacher' })} className="inline-flex items-center gap-1 px-2 py-1 rounded text-amber-700 hover:bg-amber-50 dark:text-amber-400 dark:hover:bg-amber-900/20 text-xs">
                                                <KeyRound size={12} /> 重置密码
                                            </button>
                                            <button type="button" onClick={() => handleDeleteTeacher(t.id)} className="inline-flex items-center gap-1 px-2 py-1 rounded text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20 text-xs">
                                                <Trash2 size={12} /> 删除教师
                                            </button>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </article>
                    </div>
                </section>

                {/* 公共知识库（RAG）：管理员上传后，师生对话可检索 */}
                <section className="teacher-panel rounded-2xl border border-slate-200/80 dark:border-slate-700/80 overflow-hidden">
                    <div className="px-4 py-3 border-b border-gray-200 dark:border-white/10 flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                            <Database className="text-indigo-500 dark:text-indigo-400" size={20} />
                            <div>
                                <h2 className="font-semibold text-gray-900 dark:text-gray-100">公共知识库</h2>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">上传 pdf / txt / md，索引完成后师生 AI 对话将自动检索此处内容</p>
                            </div>
                        </div>
                        <label className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors shrink-0 ${kbUploading ? 'opacity-90 cursor-wait' : 'cursor-pointer'}`}>
                            {kbUploading ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
                            {kbUploading ? '上传中…' : '上传文档'}
                            <input
                                type="file"
                                accept=".pdf,.txt,.md"
                                className="hidden"
                                disabled={kbUploading}
                                onChange={handleKbUpload}
                            />
                        </label>
                    </div>
                    <div className="p-4">
                        {kbError && (
                            <div className="mb-3 text-sm text-red-600 dark:text-red-400">{kbError}</div>
                        )}
                        {kbDocs.length === 0 ? (
                            <p className="text-sm text-gray-500 dark:text-gray-400">暂无文档。请上传德语学习资料等文件，状态为 ready 后即可在对话中被检索。</p>
                        ) : (
                            <ul className="space-y-2">
                                {kbDocs.map((d) => (
                                    <li
                                        key={d.id}
                                        className="flex flex-wrap items-center gap-2 py-2 px-3 rounded-lg bg-gray-50 dark:bg-white/5 text-sm border border-gray-100 dark:border-white/10"
                                    >
                                        <div className="flex flex-wrap items-center gap-2 min-w-0 flex-1">
                                            <span className="font-medium text-gray-800 dark:text-gray-200">{d.title}</span>
                                            <span className="text-gray-500 dark:text-gray-400">({d.source_name})</span>
                                            <span className="text-xs px-2 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                                                {d.status}
                                            </span>
                                            <span className="text-gray-500 dark:text-gray-400">切片: {d.chunk_count ?? 0}</span>
                                            {d.error_message && (
                                                <span className="text-red-500 dark:text-red-400 truncate max-w-[280px]" title={d.error_message}>
                                                    错误: {d.error_message}
                                                </span>
                                            )}
                                        </div>
                                        <div className="flex items-center gap-1 shrink-0 ml-auto">
                                            <button
                                                type="button"
                                                disabled={kbReindexingId === d.id || kbDeletingId === d.id || kbUploading}
                                                onClick={() => handleKbReindex(d.id)}
                                                className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 text-xs font-medium disabled:opacity-50 disabled:pointer-events-none"
                                            >
                                                {kbReindexingId === d.id ? (
                                                    <Loader2 size={12} className="animate-spin" />
                                                ) : (
                                                    <RefreshCw size={12} />
                                                )}
                                                {kbReindexingId === d.id ? '重建中…' : '重建索引'}
                                            </button>
                                            <button
                                                type="button"
                                                disabled={kbReindexingId === d.id || kbDeletingId === d.id || kbUploading}
                                                onClick={() => handleKbDelete(d.id, d.title)}
                                                className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 text-xs font-medium disabled:opacity-50 disabled:pointer-events-none"
                                            >
                                                {kbDeletingId === d.id ? (
                                                    <Loader2 size={12} className="animate-spin" />
                                                ) : (
                                                    <Trash2 size={12} />
                                                )}
                                                {kbDeletingId === d.id ? '删除中…' : '删除'}
                                            </button>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                </section>

                {/* 系统设置 */}
                <section className="teacher-panel rounded-2xl border border-slate-200/80 dark:border-slate-700/80 overflow-hidden">
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

            {isPendingPanelOpen && (
                <div className="fixed inset-0 z-50 bg-black/35" onClick={() => setIsPendingPanelOpen(false)}>
                    <div
                        className="absolute top-0 right-0 h-full w-full sm:w-[460px] teacher-panel border-l border-amber-200/70 dark:border-amber-900/50 p-4 sm:p-5 overflow-y-auto"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                                <UserPlus size={20} className="text-amber-500 dark:text-amber-400" />
                                待审核教师
                                {pendingTeachers.length > 0 && (
                                    <span className="ml-1 bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">{pendingTeachers.length}</span>
                                )}
                            </h3>
                            <button
                                type="button"
                                className="teacher-action-secondary px-3 py-1.5 rounded-lg text-sm"
                                onClick={() => setIsPendingPanelOpen(false)}
                            >
                                关闭
                            </button>
                        </div>
                        {pendingTeachers.length === 0 ? (
                            <div className="rounded-xl border border-slate-200 dark:border-slate-700 p-5 text-sm text-slate-500 dark:text-slate-400">
                                当前暂无待审核教师申请。
                            </div>
                        ) : (
                            <ul className="space-y-3">
                                {pendingTeachers.map((t) => (
                                    <li key={t.id} className="rounded-xl bg-amber-50 dark:bg-amber-900/12 border border-amber-200/70 dark:border-amber-900/40 p-4">
                                        <div className="mb-3">
                                            <p className="font-bold text-slate-800 dark:text-slate-100">{t.display_name}</p>
                                            <p className="text-sm text-slate-500 dark:text-slate-400">工号: {t.username}</p>
                                            <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">申请时间: {new Date(t.created_at).toLocaleString()}</p>
                                        </div>
                                        <div className="flex flex-wrap gap-2">
                                            <button
                                                type="button"
                                                onClick={() => handleApproveTeacher(t.id)}
                                                className="inline-flex items-center justify-center gap-1 px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium transition-colors"
                                            >
                                                <CheckCircle size={14} /> 允许加入
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => handleRejectTeacher(t.id)}
                                                className="inline-flex items-center justify-center gap-1 px-3 py-1.5 rounded-lg bg-red-50 hover:bg-red-100 text-red-600 dark:bg-red-900/20 dark:hover:bg-red-900/40 dark:text-red-400 text-sm font-medium transition-colors"
                                            >
                                                <XCircle size={14} /> 拒绝
                                            </button>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                </div>
            )}

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
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">负责教师（支持多选）</label>
                                    <div className="rounded-xl border border-slate-200 dark:border-slate-600 bg-slate-50/70 dark:bg-slate-900/40 p-3 space-y-2">
                                        <input
                                            type="text"
                                            value={createTeacherKeyword}
                                            onChange={(e) => setCreateTeacherKeyword(e.target.value)}
                                            placeholder="搜索教师姓名或工号"
                                            className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-600 bg-white/95 dark:bg-slate-800/80 text-sm text-slate-800 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
                                        />
                                        <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                                            <span>已选 {createClassTeacherIds.length} 位教师</span>
                                            <div className="flex items-center gap-2">
                                                <button
                                                    type="button"
                                                    className="hover:text-indigo-600 dark:hover:text-indigo-300"
                                                    onClick={() => setCreateClassTeacherIds(filteredCreateTeachers.map((t) => t.id))}
                                                >
                                                    全选当前结果
                                                </button>
                                                <button
                                                    type="button"
                                                    className="hover:text-rose-600 dark:hover:text-rose-300"
                                                    onClick={() => setCreateClassTeacherIds([])}
                                                >
                                                    清空
                                                </button>
                                            </div>
                                        </div>
                                        <div className="max-h-44 overflow-y-auto space-y-1.5 pr-1">
                                            {filteredCreateTeachers.map((t) => (
                                                <label key={t.id} className="flex items-center gap-2 rounded-lg border border-transparent hover:border-indigo-200 dark:hover:border-indigo-700/60 hover:bg-indigo-50/70 dark:hover:bg-indigo-900/25 px-2 py-1.5 cursor-pointer">
                                                    <input
                                                        type="checkbox"
                                                        checked={createClassTeacherIds.includes(t.id)}
                                                        onChange={(e) => {
                                                            setCreateClassTeacherIds((prev) => (
                                                                e.target.checked ? [...new Set([...prev, t.id])] : prev.filter((id) => id !== t.id)
                                                            ));
                                                        }}
                                                        className="h-4 w-4 rounded border-slate-300 dark:border-slate-600 text-indigo-600 focus:ring-indigo-500"
                                                    />
                                                    <span className="text-sm text-slate-800 dark:text-slate-100">{t.display_name}</span>
                                                    <span className="text-xs text-slate-500 dark:text-slate-400">({t.username})</span>
                                                </label>
                                            ))}
                                        </div>
                                    </div>
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
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">负责教师（支持多选）</label>
                                    <div className="rounded-xl border border-slate-200 dark:border-slate-600 bg-slate-50/70 dark:bg-slate-900/40 p-3 space-y-2">
                                        <input
                                            type="text"
                                            value={editClassTeacherKeyword}
                                            onChange={(e) => setEditClassTeacherKeyword(e.target.value)}
                                            placeholder="搜索教师姓名或工号"
                                            className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-600 bg-white/95 dark:bg-slate-800/80 text-sm text-slate-800 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
                                        />
                                        <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                                            <span>已选 {editClassTeacherIds.length} 位教师</span>
                                            <div className="flex items-center gap-2">
                                                <button
                                                    type="button"
                                                    className="hover:text-indigo-600 dark:hover:text-indigo-300"
                                                    onClick={() => {
                                                        const filteredIds = filteredEditClassTeachers.map((t) => t.id);
                                                        setEditClassTeacherIds((prev) => [...new Set([...prev, ...filteredIds])]);
                                                    }}
                                                >
                                                    全选当前结果
                                                </button>
                                                <button
                                                    type="button"
                                                    className="hover:text-rose-600 dark:hover:text-rose-300"
                                                    onClick={() => setEditClassTeacherIds([])}
                                                >
                                                    清空
                                                </button>
                                            </div>
                                        </div>
                                        <div className="max-h-44 overflow-y-auto space-y-1.5 pr-1">
                                            {filteredEditClassTeachers.map((t) => (
                                                <label key={t.id} className="flex items-center gap-2 rounded-lg border border-transparent hover:border-indigo-200 dark:hover:border-indigo-700/60 hover:bg-indigo-50/70 dark:hover:bg-indigo-900/25 px-2 py-1.5 cursor-pointer">
                                                    <input
                                                        type="checkbox"
                                                        checked={editClassTeacherIds.includes(t.id)}
                                                        onChange={(e) => {
                                                            setEditClassTeacherIds((prev) => (
                                                                e.target.checked ? [...new Set([...prev, t.id])] : prev.filter((id) => id !== t.id)
                                                            ));
                                                        }}
                                                        className="h-4 w-4 rounded border-slate-300 dark:border-slate-600 text-indigo-600 focus:ring-indigo-500"
                                                    />
                                                    <span className="text-sm text-slate-800 dark:text-slate-100">{t.display_name}</span>
                                                    <span className="text-xs text-slate-500 dark:text-slate-400">({t.username})</span>
                                                </label>
                                            ))}
                                        </div>
                                    </div>
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

            {/* 编辑教师弹窗 */}
            {showEditTeacherModal && editingTeacher && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={() => {
                    if (!submitLoading) {
                        setShowEditTeacherModal(false);
                        setEditTeacherClassIds([]);
                        setEditTeacherClassKeyword('');
                    }
                }}>
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-lg p-6" onClick={e => e.stopPropagation()}>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">编辑教师 · {editingTeacher.username}</h3>
                        <form onSubmit={handleEditTeacher}>
                            {formError && <p className="text-sm text-red-600 dark:text-red-400 mb-3">{formError}</p>}
                            <div className="space-y-3">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">教师姓名</label>
                                    <input name="display_name" type="text" required defaultValue={editingTeacher.display_name} className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-sm" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">所属班级（支持多选）</label>
                                    <div className="rounded-xl border border-slate-200 dark:border-slate-600 bg-slate-50/70 dark:bg-slate-900/40 p-3 space-y-2">
                                        <input
                                            type="text"
                                            value={editTeacherClassKeyword}
                                            onChange={(e) => setEditTeacherClassKeyword(e.target.value)}
                                            placeholder="搜索班级名称或代码"
                                            className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-600 bg-white/95 dark:bg-slate-800/80 text-sm text-slate-800 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
                                        />
                                        <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                                            <span>已选 {editTeacherClassIds.length} 个班级</span>
                                            <div className="flex items-center gap-2">
                                                <button
                                                    type="button"
                                                    className="hover:text-indigo-600 dark:hover:text-indigo-300"
                                                    onClick={() => {
                                                        const filteredIds = filteredEditTeacherClasses.map((c) => c.id);
                                                        setEditTeacherClassIds((prev) => [...new Set([...prev, ...filteredIds])]);
                                                    }}
                                                >
                                                    全选当前结果
                                                </button>
                                                <button
                                                    type="button"
                                                    className="hover:text-rose-600 dark:hover:text-rose-300"
                                                    onClick={() => setEditTeacherClassIds([])}
                                                >
                                                    清空
                                                </button>
                                            </div>
                                        </div>
                                        <div className="max-h-44 overflow-y-auto space-y-1.5 pr-1">
                                            {filteredEditTeacherClasses.map((c) => (
                                                <label key={c.id} className="flex items-center gap-2 rounded-lg border border-transparent hover:border-indigo-200 dark:hover:border-indigo-700/60 hover:bg-indigo-50/70 dark:hover:bg-indigo-900/25 px-2 py-1.5 cursor-pointer">
                                                    <input
                                                        type="checkbox"
                                                        checked={editTeacherClassIds.includes(c.id)}
                                                        onChange={(e) => {
                                                            setEditTeacherClassIds((prev) => (
                                                                e.target.checked ? [...new Set([...prev, c.id])] : prev.filter((id) => id !== c.id)
                                                            ));
                                                        }}
                                                        className="h-4 w-4 rounded border-slate-300 dark:border-slate-600 text-indigo-600 focus:ring-indigo-500"
                                                    />
                                                    <span className="text-sm text-slate-800 dark:text-slate-100">{c.class_name}</span>
                                                    <span className="text-xs text-slate-500 dark:text-slate-400">({c.class_code})</span>
                                                </label>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="flex gap-2 mt-6">
                                <button
                                    type="button"
                                    onClick={() => {
                                        if (!submitLoading) {
                                            setShowEditTeacherModal(false);
                                            setEditTeacherClassIds([]);
                                            setEditTeacherClassKeyword('');
                                        }
                                    }}
                                    className="flex-1 py-2 rounded-lg border border-gray-200 dark:border-white/10 text-gray-700 dark:text-gray-300 text-sm font-medium"
                                >
                                    取消
                                </button>
                                <button type="submit" disabled={submitLoading} className="flex-1 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium disabled:opacity-50">{submitLoading ? '保存中…' : '保存'}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* 编辑学生弹窗 */}
            {editingStudent && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={() => !submitLoading && setEditingStudent(null)}>
                    <div className="teacher-panel rounded-2xl shadow-xl w-full max-w-md p-4 sm:p-6" onClick={e => e.stopPropagation()}>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">编辑学生信息 · {editingStudent.uid}</h3>
                        <form onSubmit={handleEditStudent}>
                            {formError && <p className="text-sm text-red-600 dark:text-red-400 mb-3">{formError}</p>}
                            <div className="space-y-3">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">姓名</label>
                                    <input name="name" type="text" required defaultValue={editingStudent.name} className="teacher-input w-full px-3 py-2 rounded-lg text-sm" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">班级</label>
                                    <select name="class_id" defaultValue={editingStudent.class_id ?? ''} className="teacher-input w-full px-3 py-2 rounded-lg text-sm">
                                        <option value="">未分班</option>
                                        {classes.map(c => <option key={c.id} value={c.id}>{c.class_name} ({c.class_code})</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">状态</label>
                                    <select name="status" defaultValue={editingStudent.status || 'approved'} className="teacher-input w-full px-3 py-2 rounded-lg text-sm">
                                        <option value="approved">审核通过</option>
                                        <option value="pending">待审核</option>
                                        <option value="rejected">已拒绝</option>
                                    </select>
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">活跃度（系统测量）</label>
                                        <input type="text" readOnly value={`${editingStudent.active_score ?? 0}%`} className="teacher-input w-full px-3 py-2 rounded-lg text-sm text-gray-500 dark:text-gray-400" />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">综合分（系统测量）</label>
                                        <input type="text" readOnly value={`${editingStudent.overall_score ?? 0} 分`} className="teacher-input w-full px-3 py-2 rounded-lg text-sm text-gray-500 dark:text-gray-400" />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">薄弱点（选填）</label>
                                    <input name="weak_point" type="text" defaultValue={editingStudent.weak_point ?? ''} className="teacher-input w-full px-3 py-2 rounded-lg text-sm" />
                                </div>
                            </div>
                            <div className="flex gap-2 mt-6">
                                <button type="button" onClick={() => !submitLoading && setEditingStudent(null)} className="teacher-action-secondary flex-1 py-2 rounded-lg text-sm font-medium">取消</button>
                                <button type="submit" disabled={submitLoading} className="teacher-action-primary flex-1 py-2 rounded-lg text-sm font-medium disabled:opacity-50">{submitLoading ? '保存中…' : '保存'}</button>
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
