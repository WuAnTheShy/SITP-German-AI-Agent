import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { parseStoredUserInfo } from '../../utils/safeJson';
import request from '../../api/request';
import { LayoutDashboard, LogOut, Users, FileText, Activity, ArrowRight, TrendingUp, Clock, Search, Loader2, Bot, RefreshCw, Plus, GraduationCap, Award, Key, UserPlus, CheckCircle, XCircle, Pencil, Trash2 } from 'lucide-react';
import { API_DASHBOARD, API_TEACHER_PENDING_STUDENTS, API_TEACHER_APPROVE_STUDENT, API_TEACHER_REJECT_STUDENT, API_TEACHER_STUDENTS, API_TEACHER_UPDATE_STUDENT, API_TEACHER_REMOVE_STUDENT } from '../../api/config';
import { useToast } from '../../components/Toast';
import PasswordChangeModal from '../../components/PasswordChangeModal';

const TeacherDashboard = () => {
    const navigate = useNavigate();
    const toast = useToast();

    // 状态管理
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState(null);
    const [pendingStudents, setPendingStudents] = useState([]);
    const [classStudents, setClassStudents] = useState([]);
    const [error, setError] = useState('');
    const [searchTerm, setSearchTerm] = useState('');
    const [refreshing, setRefreshing] = useState(false);
    const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
    const [editingStudent, setEditingStudent] = useState(null);
    const [studentFormError, setStudentFormError] = useState('');
    const [studentSubmitLoading, setStudentSubmitLoading] = useState(false);
    const [isPendingPanelOpen, setIsPendingPanelOpen] = useState(false);

    // 🟢 从 localStorage 读取教师名称
    const userInfo = parseStoredUserInfo();
    const teacherName = userInfo.name || data?.teacherName || '老师';

    const normalizeArrayPayload = useCallback((res) => {
        const payload = res?.data;
        if (Array.isArray(payload?.data)) return payload.data;
        if (Array.isArray(payload)) return payload;
        return [];
    }, []);

    // 🟢 获取仪表盘数据（可复用）
    const fetchDashboardData = useCallback(async (showRefreshToast = false) => {
        if (showRefreshToast) setRefreshing(true);
        else setLoading(true);

        try {
            console.log('[Client] 正在加载仪表盘数据...');
            const [dashboardRes, pendingRes, studentsRes] = await Promise.all([
                request.get(API_DASHBOARD),
                request.get(API_TEACHER_PENDING_STUDENTS).catch(() => ({ data: { data: [] } })),
                request.get(API_TEACHER_STUDENTS).catch(() => ({ data: { data: [] } }))
            ]);

            if (dashboardRes.data.code === 200) {
                setData(dashboardRes.data.data);
                setPendingStudents(normalizeArrayPayload(pendingRes));
                setClassStudents(normalizeArrayPayload(studentsRes));
                setError('');
                if (showRefreshToast) toast.success('数据刷新成功');
            } else {
                throw new Error(dashboardRes.data.message || '数据加载失败');
            }
        } catch (err) {
            console.error('加载失败:', err);
            setData(FALLBACK_DATA);
            setPendingStudents([]);
            setClassStudents([]);
            setError('网络请求失败，已切换至离线模式');
            if (showRefreshToast) toast.error('刷新失败，使用缓存数据');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, [normalizeArrayPayload, toast]);

    // 初始化
    useEffect(() => {
        fetchDashboardData(false);
    }, [fetchDashboardData]);

    const handleLogout = () => {
        localStorage.removeItem('authToken');
        localStorage.removeItem('userInfo');
        navigate('/');
    };

    const handleApproveStudent = async (id) => {
        try {
            const res = await request.put(API_TEACHER_APPROVE_STUDENT(id));
            if(res.data.code === 200) {
                 toast.success('审批通过');
                 fetchDashboardData();
            } else {
                 toast.error(res.data.message || '审批失败');
            }
        } catch(err) {
            toast.error(err.response?.data?.detail || '审批出错');
        }
    };

    const handleRejectStudent = async (id) => {
        if(!window.confirm('确定拒绝该学生加入班级吗？')) return;
        try {
            const res = await request.put(API_TEACHER_REJECT_STUDENT(id));
            if(res.data.code === 200) {
                 toast.success('已拒绝加入');
                 fetchDashboardData();
            } else {
                 toast.error(res.data.message || '拒绝失败');
            }
        } catch(err) {
            toast.error(err.response?.data?.detail || '操作出错');
        }
    };

    const openEditStudentModal = (student) => {
        setEditingStudent(student);
        setStudentFormError('');
    };

    const handleUpdateStudent = async (e) => {
        e.preventDefault();
        if (!editingStudent) return;

        const form = e.target;
        const payload = {
            name: (form.name?.value || '').trim(),
            status: form.status?.value,
            weak_point: (form.weak_point?.value || '').trim() || null,
        };

        if (!payload.name) {
            setStudentFormError('姓名不能为空');
            return;
        }

        setStudentSubmitLoading(true);
        try {
            const res = await request.put(API_TEACHER_UPDATE_STUDENT(editingStudent.id), payload);
            if (res.data.code === 200) {
                toast.success('学生信息已更新');
                setEditingStudent(null);
                fetchDashboardData();
            } else {
                setStudentFormError(res.data.message || '保存失败');
            }
        } catch (err) {
            setStudentFormError(err.response?.data?.detail || '保存失败');
        } finally {
            setStudentSubmitLoading(false);
        }
    };

    const handleRemoveStudent = async (id) => {
        if (!window.confirm('确定将该学生移出当前班级吗？')) return;
        try {
            const res = await request.delete(API_TEACHER_REMOVE_STUDENT(id));
            if (res.data.code === 200) {
                toast.success('学生已移出班级');
                fetchDashboardData();
            } else {
                toast.error(res.data.message || '操作失败');
            }
        } catch (err) {
            toast.error(err.response?.data?.detail || '移出失败');
        }
    };

    // 过滤学生列表（增加判空容错和大小写不敏感搜索）
    const filteredStudents = useMemo(() => {
        const keyword = searchTerm.trim().toLowerCase();
        return classStudents.filter((s) => {
            if (!keyword) return true;
            const nameMatch = s?.name ? s.name.toLowerCase().includes(keyword) : false;
            const uidMatch = s?.uid ? String(s.uid).toLowerCase().includes(keyword) : false;
            const classMatch = Array.isArray(s?.class_names)
                ? s.class_names.some((name) => String(name || '').toLowerCase().includes(keyword))
                : String(s?.class_name || '').toLowerCase().includes(keyword);
            return nameMatch || uidMatch || classMatch;
        });
    }, [classStudents, searchTerm]);

    // 一个教师管理多个班级时，学生按班级分组显示
    const groupedStudents = useMemo(() => {
        const groups = new Map();
        filteredStudents.forEach((student) => {
            const classNames = Array.isArray(student?.class_names) && student.class_names.length > 0
                ? student.class_names
                : [student?.class_name || '未分班'];

            classNames.forEach((classNameRaw) => {
                const className = String(classNameRaw || '未分班');
                const list = groups.get(className) || [];
                if (!list.some((x) => x.id === student.id)) {
                    list.push(student);
                }
                groups.set(className, list);
            });
        });

        return Array.from(groups.entries())
            .map(([className, students]) => ({ className, students }))
            .sort((a, b) => a.className.localeCompare(b.className, 'zh-CN'));
    }, [filteredStudents]);

    // 渲染加载状态
    if (loading) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-900">
                <Loader2 size={40} className="text-indigo-600 dark:text-indigo-400 animate-spin mb-4" />
                <p className="text-gray-500 dark:text-gray-400 font-medium">正在同步班级学情数据...</p>
            </div>
        );
    }

    // 渲染主界面（未关联班级时后端返回 className: "未关联"、students: []，同屏正常展示）
    return (
        <div className="teacher-shell p-3 sm:p-4 md:p-8">
            <div className="max-w-7xl mx-auto space-y-6 md:space-y-8">

                {/* 1. 页面标题区（与功能按钮分离） */}
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 sm:gap-4">
                    <div>
                        <h1 className="text-xl sm:text-2xl md:text-3xl teacher-section-title flex items-center gap-2 sm:gap-3">
                            <LayoutDashboard className="text-teal-700 dark:text-teal-300 shrink-0" />
                            <span>教师控制台</span>
                        </h1>
                        <p className="text-xs sm:text-sm md:text-base text-gray-500 dark:text-gray-400 mt-1.5 sm:mt-2">欢迎回来，{teacherName}。今日有 {data?.pendingTasks || 0} 条新的学情动态。</p>
                    </div>
                    <div className="teacher-panel rounded-2xl px-3 sm:px-4 py-3 flex flex-col gap-2.5 w-full sm:w-auto shrink-0">
                        <div className="flex items-center gap-3">
                            <div className="h-11 w-11 rounded-full bg-teal-100 dark:bg-teal-900/40 text-teal-700 dark:text-teal-300 font-bold flex items-center justify-center">
                                {(teacherName || '教')[0]}
                            </div>
                            <div className="min-w-0">
                                <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 truncate max-w-[150px]">{teacherName}</p>
                                <p className="text-xs text-slate-500 dark:text-slate-400">教师账号</p>
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            <button
                                type="button"
                                onClick={() => setIsPasswordModalOpen(true)}
                                className="teacher-action-secondary h-9 px-3 rounded-xl text-xs sm:text-sm font-medium flex items-center justify-center gap-1.5"
                            >
                                <Key size={14} /> 修改密码
                            </button>
                            <button
                                type="button"
                                onClick={handleLogout}
                                className="h-9 px-3 rounded-xl text-xs sm:text-sm font-medium flex items-center justify-center gap-1.5 bg-red-50 dark:bg-red-900/25 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800/40 hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors"
                            >
                                <LogOut size={14} /> 退出登录
                            </button>
                        </div>
                    </div>
                </div>
                </div>

                {/* 2. 班级信息区 */}
                <div className="teacher-panel rounded-2xl p-3 sm:p-4 md:p-5 flex flex-wrap items-center gap-2">
                    <span className="text-xs md:text-sm font-normal text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700/60 px-2 py-0.5 rounded-md">
                        班级：{data?.className || '加载中...'}
                    </span>
                    {data?.classCode && (
                        <button
                            type="button"
                            className="text-xs md:text-sm font-normal text-teal-700 dark:text-teal-300 bg-teal-50 dark:bg-teal-900/30 px-2 py-0.5 rounded-md flex items-center gap-1.5 hover:bg-teal-100 dark:hover:bg-teal-900/50 transition-colors"
                            onClick={() => {
                                navigator.clipboard.writeText(data.classCode);
                                alert('班级邀请码已复制：' + data.classCode);
                            }}
                            title="点击复制邀请码"
                        >
                            <Key size={14} />
                            邀请码: <span className="font-mono font-bold tracking-wider">{data.classCode}</span>
                        </button>
                    )}
                </div>

                {/* 3. 操作按钮区 */}
                <div className="teacher-panel rounded-2xl p-3 sm:p-4 md:p-6">
                    <div className="w-full grid grid-cols-1 xl:grid-cols-2 gap-3">
                        <div className="rounded-xl border border-slate-200/80 dark:border-slate-700/80 p-3 bg-white/50 dark:bg-slate-900/50">
                            <p className="text-xs font-semibold tracking-wide text-slate-500 dark:text-slate-400 mb-2">教务操作</p>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                <button
                                    type="button"
                                    onClick={() => navigate(`/teacher/${userInfo.id}/scenario`)}
                                    className="teacher-action-primary h-10 px-4 rounded-xl font-bold flex items-center gap-2 text-sm"
                                >
                                    <Plus size={16} /> 发布任务
                                </button>
                                <button
                                    type="button"
                                    onClick={() => navigate(`/teacher/${userInfo.id}/exam`)}
                                    className="h-10 px-4 rounded-xl font-bold flex items-center gap-2 transition-colors text-sm bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-900/50 border border-emerald-200 dark:border-emerald-800/40"
                                >
                                    <GraduationCap size={16} /> 生成试卷
                                </button>
                                <button
                                    type="button"
                                    onClick={() => navigate(`/teacher/${userInfo.id}/ai`)}
                                    className="h-10 px-4 rounded-xl font-bold flex items-center gap-2 transition-colors text-sm bg-sky-50 dark:bg-sky-900/30 text-sky-700 dark:text-sky-300 hover:bg-sky-100 dark:hover:bg-sky-900/50 border border-sky-200 dark:border-sky-800/40"
                                >
                                    <Bot size={16} /> AI 助手
                                </button>
                            </div>
                        </div>
                        <div className="rounded-xl border border-slate-200/80 dark:border-slate-700/80 p-3 bg-white/50 dark:bg-slate-900/50">
                            <p className="text-xs font-semibold tracking-wide text-slate-500 dark:text-slate-400 mb-2">班级与系统</p>
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                <button
                                    type="button"
                                    onClick={() => setIsPendingPanelOpen(true)}
                                    className="teacher-action-secondary h-10 px-4 rounded-xl font-medium flex items-center gap-2 text-sm"
                                >
                                    <UserPlus size={16} /> 审核学生
                                    {pendingStudents.length > 0 && (
                                        <span className="inline-flex items-center justify-center min-w-5 h-5 px-1 rounded-full bg-red-500 text-white text-xs font-bold">
                                            {pendingStudents.length}
                                        </span>
                                    )}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => fetchDashboardData(true)}
                                    disabled={refreshing}
                                    className="teacher-action-secondary h-10 px-4 rounded-xl font-medium flex items-center gap-2 text-sm disabled:opacity-50"
                                >
                                    <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} /> 刷新
                                </button>
                                <button
                                    type="button"
                                    onClick={() => navigate(`/teacher/${userInfo.id}/history`)}
                                    className="teacher-action-secondary h-10 px-4 rounded-xl font-medium flex items-center gap-2 text-sm"
                                >
                                    <FileText size={16} /> 作业记录
                                </button>
                            </div>
                    </div>
                </div>

                {/* 错误提示 */}
                {error && (
                    <div className="bg-orange-50 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 px-4 py-3 rounded-xl flex items-center gap-2 border border-orange-100 dark:border-orange-900/50">
                        <Activity size={18} /> {error}
                    </div>
                )}

                {/* 2. 核心指标卡片 (Stats) - 🟢 全部动态化 */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
                    <StatCard
                        icon={<Users className="text-blue-600 dark:text-blue-400" />}
                        label="班级总人数"
                        value={data?.stats?.totalStudents || 0}
                        trend={data?.stats?.totalStudentsTrend || '-'} // 动态趋势
                        bg="bg-blue-50 dark:bg-blue-900/30"
                    />
                    <StatCard
                        icon={<Clock className="text-purple-600" />}
                        label="人均互动时长"
                        value={`${data?.stats?.avgDuration || 0} h`}
                        trend={data?.stats?.avgDurationTrend || '-'} // 动态趋势
                        bg="bg-purple-50 dark:bg-purple-900/30"
                    />
                    <StatCard
                        icon={<Award className="text-orange-600 dark:text-orange-400" />}
                        label="平均综合得分"
                        value={data?.stats?.avgScore || 0}
                        trend={data?.stats?.avgScoreTrend || '-'} // 动态趋势
                        bg="bg-orange-50 dark:bg-orange-900/30"
                    />
                    <StatCard
                        icon={<TrendingUp className="text-green-600" />}
                        label="任务完成率"
                        value={`${data?.stats?.completionRate || 0}% `}
                        trend={data?.stats?.completionRateTrend || '-'} // 动态趋势
                        bg="bg-green-50 dark:bg-green-900/30"
                    />
                </div>

                {/* 3. 学生列表区块 */}
                <div className="teacher-panel rounded-2xl overflow-hidden">
                    {/* 列表头部工具栏 */}
                    <div className="p-4 sm:p-6 border-b border-gray-100 dark:border-gray-700 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
                        <h2 className="text-lg font-bold text-gray-800 dark:text-gray-200 flex items-center gap-2">
                            <Users size={20} className="text-indigo-600 dark:text-indigo-400" /> 学情监控列表
                        </h2>
                        <div className="relative w-full sm:w-auto">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500" size={18} />
                            <input
                                type="text"
                                placeholder="搜索姓名或学号..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="teacher-input pl-10 pr-4 py-2 rounded-lg text-sm w-full sm:w-64 transition-all"
                            />
                        </div>
                    </div>

                    {/* 表格（桌面端）按班级分组 */}
                    <div className="hidden md:block space-y-4 px-4 pb-4">
                        {groupedStudents.map((group) => (
                            <section key={group.className} className="rounded-xl border border-slate-200/80 dark:border-slate-700/80 overflow-hidden">
                                <div className="px-4 py-3 bg-slate-50/90 dark:bg-slate-900/60 border-b border-slate-200/80 dark:border-slate-700/80 flex items-center justify-between">
                                    <div className="text-sm font-semibold text-slate-700 dark:text-slate-200">{group.className}</div>
                                    <div className="text-xs text-slate-500 dark:text-slate-400">{group.students.length} 人</div>
                                </div>
                                <div className="overflow-x-auto">
                                    <table className="w-full min-w-[920px]">
                                        <thead className="bg-slate-50/60 dark:bg-slate-900/50 border-b border-slate-200/80 dark:border-slate-700">
                                            <tr>
                                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">学生信息</th>
                                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">活跃度</th>
                                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">综合评分</th>
                                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">薄弱环节</th>
                                                <th className="px-6 py-4 text-right text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">操作</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                                            {group.students.map((student) => (
                                                <tr
                                                    key={`${group.className}-${student.id || student.uid}`}
                                                    onClick={() => navigate(`/teacher/${userInfo.id}/student/${student.uid}`, { state: { student } })}
                                                    className="hover:bg-teal-50/70 dark:hover:bg-teal-900/20 transition-colors cursor-pointer group"
                                                >
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <div className="flex items-center">
                                                            <div className="flex-shrink-0 h-10 w-10 bg-teal-100 dark:bg-teal-900/40 rounded-full flex items-center justify-center text-teal-700 dark:text-teal-300 font-bold">
                                                                {(student.name || '匿')[0]}
                                                            </div>
                                                            <div className="ml-4">
                                                                <div className="text-sm font-bold text-gray-900 dark:text-gray-100">{student.name || '匿名用户'}</div>
                                                                <div className="text-xs text-gray-500 dark:text-gray-400">{student.uid || '无学号'}</div>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <div className="flex items-center gap-2">
                                                            <div className="w-16 h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                                                                <div className="h-full bg-green-500" style={{ width: `${Math.max(0, Math.min(100, Number(student.active_score ?? 0)))}%` }}></div>
                                                            </div>
                                                            <span className="text-sm text-gray-600 dark:text-gray-400">{Number(student.active_score ?? 0)}%</span>
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${Number(student.overall_score ?? 0) >= 90 ? 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-400' : Number(student.overall_score ?? 0) >= 80 ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-400' : 'bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-400'}`}>
                                                            {Number(student.overall_score ?? 0).toFixed(1)} 分
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                                        <span className="flex items-center gap-1 text-red-500 dark:text-red-400 bg-red-50 dark:bg-red-900/30 px-2 py-0.5 rounded w-fit">
                                                            <Activity size={12} /> {student.weak_point || '暂无'}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                        <div className="flex justify-end items-center gap-1">
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    openEditStudentModal(student);
                                                                }}
                                                                className="inline-flex items-center gap-1 text-teal-700 dark:text-teal-300 hover:text-teal-900 dark:hover:text-teal-200 p-2 hover:bg-teal-50 dark:hover:bg-teal-900/50 rounded-lg transition-colors"
                                                            >
                                                                <Pencil size={16} />
                                                            </button>
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    handleRemoveStudent(student.id);
                                                                }}
                                                                className="inline-flex items-center gap-1 text-red-600 dark:text-red-400 p-2 hover:bg-red-50 dark:hover:bg-red-900/50 rounded-lg transition-colors"
                                                            >
                                                                <Trash2 size={16} />
                                                            </button>
                                                            <button className="text-teal-700 dark:text-teal-300 hover:text-teal-900 dark:hover:text-teal-200 p-2 hover:bg-teal-50 dark:hover:bg-teal-900/50 rounded-lg transition-colors">
                                                                <ArrowRight size={18} />
                                                            </button>
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </section>
                        ))}
                    </div>

                    {/* 卡片（移动端）按班级分组 */}
                    <div className="md:hidden space-y-3 p-3">
                        {groupedStudents.map((group) => (
                            <section key={`mobile-${group.className}`} className="rounded-xl border border-slate-200/80 dark:border-slate-700/80 overflow-hidden">
                                <div className="px-3 py-2.5 bg-slate-50/90 dark:bg-slate-900/60 border-b border-slate-200/80 dark:border-slate-700/80 flex items-center justify-between">
                                    <div className="text-sm font-semibold text-slate-700 dark:text-slate-200 truncate">{group.className}</div>
                                    <div className="text-xs text-slate-500 dark:text-slate-400">{group.students.length} 人</div>
                                </div>
                                <div className="divide-y divide-slate-200/80 dark:divide-slate-700/70">
                                    {group.students.map((student) => (
                                        <div
                                            key={`mobile-${group.className}-${student.id || student.uid}`}
                                            onClick={() => navigate(`/teacher/${userInfo.id}/student/${student.uid}`, { state: { student } })}
                                            className="p-4 active:bg-slate-50 dark:active:bg-slate-800/50"
                                        >
                                            <div className="flex items-center justify-between gap-3">
                                                <div className="flex items-center gap-3 min-w-0">
                                                    <div className="h-9 w-9 bg-teal-100 dark:bg-teal-900/40 rounded-full flex items-center justify-center text-teal-700 dark:text-teal-300 font-bold shrink-0">
                                                        {(student.name || '匿')[0]}
                                                    </div>
                                                    <div className="min-w-0">
                                                        <p className="text-sm font-bold text-slate-900 dark:text-slate-100 truncate">{student.name || '匿名用户'}</p>
                                                        <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{student.uid || '无学号'}</p>
                                                    </div>
                                                </div>
                                                <span className={`px-2 py-1 inline-flex text-xs font-semibold rounded-full ${Number(student.overall_score ?? 0) >= 90 ? 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-400' : Number(student.overall_score ?? 0) >= 80 ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-400' : 'bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-400'}`}>
                                                    {Number(student.overall_score ?? 0).toFixed(1)} 分
                                                </span>
                                            </div>
                                            <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                                                <div className="rounded-lg bg-slate-100 dark:bg-slate-800 px-2.5 py-2">
                                                    <p className="text-slate-500 dark:text-slate-400">活跃度</p>
                                                    <p className="text-slate-700 dark:text-slate-200 font-semibold">{Number(student.active_score ?? 0)}%</p>
                                                </div>
                                                <div className="rounded-lg bg-red-50 dark:bg-red-900/20 px-2.5 py-2">
                                                    <p className="text-slate-500 dark:text-slate-400">薄弱点</p>
                                                    <p className="text-red-600 dark:text-red-400 font-semibold truncate">{student.weak_point || '暂无'}</p>
                                                </div>
                                            </div>
                                            <div className="mt-3 flex items-center justify-end gap-1">
                                                <button
                                                    type="button"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        openEditStudentModal(student);
                                                    }}
                                                    className="inline-flex items-center gap-1 text-teal-700 dark:text-teal-300 p-2 rounded-lg hover:bg-teal-50 dark:hover:bg-teal-900/50"
                                                >
                                                    <Pencil size={16} />
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleRemoveStudent(student.id);
                                                    }}
                                                    className="inline-flex items-center gap-1 text-red-600 dark:text-red-400 p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/50"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                                <button type="button" className="text-teal-700 dark:text-teal-300 p-2 rounded-lg hover:bg-teal-50 dark:hover:bg-teal-900/50">
                                                    <ArrowRight size={18} />
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </section>
                        ))}
                    </div>
                    {groupedStudents.length === 0 && (
                        <div className="p-8 sm:p-12 text-center text-gray-500 dark:text-gray-400 text-sm sm:text-base">
                            {!(classStudents.length) && (data?.className === '未关联')
                                ? '暂无学生。请联系管理员在「管理员工作台」为您分配班级后，即可使用任务发布、学情查看等功能。'
                                : '未找到匹配的学生'}
                        </div>
                    )}
                </div>
            </div>

            <PasswordChangeModal
                isOpen={isPasswordModalOpen}
                onClose={() => setIsPasswordModalOpen(false)}
            />

            {editingStudent && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={() => !studentSubmitLoading && setEditingStudent(null)}>
                    <div className="teacher-panel rounded-2xl shadow-xl w-full max-w-md p-4 sm:p-6" onClick={e => e.stopPropagation()}>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">编辑学生信息 · {editingStudent.uid}</h3>
                        <form onSubmit={handleUpdateStudent}>
                            {studentFormError && <p className="text-sm text-red-600 dark:text-red-400 mb-3">{studentFormError}</p>}
                            <div className="space-y-3">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">姓名</label>
                                    <input name="name" type="text" required defaultValue={editingStudent.name} className="teacher-input w-full px-3 py-2 rounded-lg text-sm" />
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
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">综合评分（系统测量）</label>
                                        <input type="text" readOnly value={`${editingStudent.overall_score ?? 0} 分`} className="teacher-input w-full px-3 py-2 rounded-lg text-sm text-gray-500 dark:text-gray-400" />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">薄弱点（选填）</label>
                                    <input name="weak_point" type="text" defaultValue={editingStudent.weak_point ?? ''} className="teacher-input w-full px-3 py-2 rounded-lg text-sm" />
                                </div>
                            </div>
                            <div className="flex gap-2 mt-6">
                                <button type="button" onClick={() => !studentSubmitLoading && setEditingStudent(null)} className="teacher-action-secondary flex-1 py-2 rounded-lg text-sm font-medium">取消</button>
                                <button type="submit" disabled={studentSubmitLoading} className="teacher-action-primary flex-1 py-2 rounded-lg text-sm font-medium disabled:opacity-50">{studentSubmitLoading ? '保存中…' : '保存'}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {isPendingPanelOpen && (
                <div className="fixed inset-0 z-50 bg-black/35" onClick={() => setIsPendingPanelOpen(false)}>
                    <div
                        className="absolute top-0 right-0 h-full w-full sm:w-[460px] teacher-panel border-l border-amber-200/70 dark:border-amber-900/50 p-4 sm:p-5 overflow-y-auto"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                                <UserPlus size={20} className="text-amber-500 dark:text-amber-400" />
                                待审核学生
                                {pendingStudents.length > 0 && (
                                    <span className="ml-1 bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">{pendingStudents.length}</span>
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
                        {pendingStudents.length === 0 ? (
                            <div className="rounded-xl border border-slate-200 dark:border-slate-700 p-5 text-sm text-slate-500 dark:text-slate-400">
                                当前暂无待审核申请。
                            </div>
                        ) : (
                            <ul className="space-y-3">
                                {pendingStudents.map((s) => (
                                    <li key={s.id} className="rounded-xl bg-amber-50 dark:bg-amber-900/12 border border-amber-200/70 dark:border-amber-900/40 p-4">
                                        <div className="mb-3">
                                            <p className="font-bold text-slate-800 dark:text-slate-100">{s.name}</p>
                                            <p className="text-sm text-slate-500 dark:text-slate-400">学号: {s.uid}</p>
                                            <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">申请时间: {new Date(s.created_at).toLocaleString()}</p>
                                        </div>
                                        <div className="flex flex-wrap gap-2">
                                            <button
                                                onClick={() => handleApproveStudent(s.id)}
                                                className="inline-flex items-center justify-center gap-1 px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium transition-colors"
                                            >
                                                <CheckCircle size={14} /> 允许加入
                                            </button>
                                            <button
                                                onClick={() => handleRejectStudent(s.id)}
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
        </div>
    );
};

// 子组件：指标卡片 (支持 trend 颜色变化逻辑)
const StatCard = ({ icon, label, value, trend, bg }) => {
    // 简单的逻辑判断趋势颜色：以 "+" 或 "↑" 开头为绿色，否则为中性色
    const isPositive = trend.includes('+') || trend.includes('↑');

    return (
        <div className="teacher-panel p-6 rounded-2xl border border-slate-200/70 dark:border-slate-700/80 hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start mb-4">
                <div className={`p-3 rounded-xl ${bg}`}>{icon}</div>
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${isPositive ? 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/30' : 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900'}`}>
                    {trend}
                </span>
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1">{value}</div>
            <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
        </div>
    );
};

// 仅在网络异常时兜底，人数与列表一致，避免「45 人但只列 2 人」等误导
const FALLBACK_DATA = {
    teacherName: '老师 (离线)',
    className: '—',
    pendingTasks: 0,
    stats: {
        totalStudents: 0,
        totalStudentsTrend: '+0',
        avgDuration: 0,
        avgDurationTrend: '—',
        avgScore: 0,
        avgScoreTrend: '—',
        completionRate: 0,
        completionRateTrend: '—'
    },
    students: []
};

export default TeacherDashboard;