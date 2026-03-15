import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Bot,
  MessageSquare,
  ScrollText,
  Headphones,
  BookMarked,
  PenLine,
  BarChart3,
  BookX,
  Star,
  LogOut,
  ClipboardList,
  Menu,
  X,
  Key,
  School,
} from "lucide-react";
import request from "../api/request";
import { API_STUDENT_CLASSES, API_STUDENT_JOIN_CLASS } from "../api/config";
import PasswordChangeModal from "./PasswordChangeModal";

const StudentLayout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false);
  const [isPasswordModalOpen, setIsPasswordModalOpen] = React.useState(false);
  const [userInfo, setUserInfo] = React.useState(() => JSON.parse(localStorage.getItem('userInfo') || '{}'));
  const [showJoinClassModal, setShowJoinClassModal] = React.useState(false);
  const [classList, setClassList] = React.useState([]);
  const [joinClassLoading, setJoinClassLoading] = React.useState(false);
  const [joinClassError, setJoinClassError] = React.useState('');

  const userId = userInfo.id || userInfo.studentId || '';
  const userName = userInfo.name || '未登录';
  const initials = userName.slice(0, 1);
  const hasClass = userInfo.classId != null && userInfo.classId !== '';

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userInfo');
    navigate('/');
  };

  const openJoinClassModal = async () => {
    setShowJoinClassModal(true);
    setJoinClassError('');
    try {
      const res = await request.get(API_STUDENT_CLASSES);
      setClassList(Array.isArray(res.data) ? res.data : []);
    } catch (e) {
      setJoinClassError(e.response?.data?.detail || e.message || '加载班级列表失败');
      setClassList([]);
    }
  };

  const handleJoinClass = async (e) => {
    e.preventDefault();
    const classId = parseInt(e.target.class_id?.value, 10);
    if (!classId) return;
    setJoinClassLoading(true);
    setJoinClassError('');
    try {
      const res = await request.post(API_STUDENT_JOIN_CLASS, { class_id: classId });
      const name = res.data?.data?.class_name || '';
      const next = { ...userInfo, classId, className: name };
      localStorage.setItem('userInfo', JSON.stringify(next));
      setUserInfo(next);
      setShowJoinClassModal(false);
    } catch (e) {
      setJoinClassError(e.response?.data?.message || e.response?.data?.detail || e.message || '加入失败');
    } finally {
      setJoinClassLoading(false);
    }
  };

  const navItems = [
    { label: "任务中心", icon: ClipboardList, path: `/student/${userId}/tasks` },
    { label: "智能对话", icon: Bot, path: `/student/${userId}/home` },
    { label: "场景对话", icon: MessageSquare, path: `/student/${userId}/ai-scene-chat` },
    { label: "语法练习", icon: ScrollText, path: `/student/${userId}/grammar-practice` },
    { label: "听说训练", icon: Headphones, path: `/student/${userId}/listening-speaking` },
    { label: "词汇学习", icon: BookMarked, path: `/student/${userId}/vocab-learning` },
    { label: "写作助手", icon: PenLine, path: `/student/${userId}/writing-assistant` },
    { label: "学习进度", icon: BarChart3, path: `/student/${userId}/learning-progress` },
    { label: "错题本复习", icon: BookX, path: `/student/${userId}/error-book` },
    { label: "我的收藏", icon: Star, path: `/student/${userId}/favorites` },
  ];

  const handleNavClick = (path) => {
    navigate(path);
    setIsMobileMenuOpen(false);
  };

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900 overflow-hidden relative">
      {/* 📱 移动端顶部状态栏 */}
      <div className="md:hidden flex items-center justify-between p-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 w-full fixed top-0 z-40">
        <h2 className="text-xl font-bold text-blue-900 dark:text-blue-400 flex items-center gap-2">
          <Bot size={24} /> AI-Tutor
        </h2>
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
        >
          {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* 遮罩层 (Mobile Overlay) */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* 🏠 左侧导航栏 - 响应式配置 */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col shrink-0
        transition-transform duration-300 ease-in-out md:relative md:translate-x-0
        ${isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"}
      `}>
        <div className="p-6 border-b border-gray-100 dark:border-gray-700 hidden md:block">
          <h2 className="text-xl font-bold text-blue-900 dark:text-blue-400 flex items-center gap-2">
            <Bot size={24} /> AI-Tutor
          </h2>
        </div>

        {/* Mobile Header (inside sidebar) */}
        <div className="p-6 border-b border-gray-100 dark:border-gray-700 flex md:hidden items-center justify-between">
          <h2 className="text-xl font-bold text-blue-900 dark:text-blue-400">导航菜单</h2>
          <button onClick={() => setIsMobileMenuOpen(false)} className="p-1 text-gray-400"><X size={20} /></button>
        </div>

        <nav className="flex-1 p-4 space-y-2 overflow-y-auto custom-scrollbar">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <button
                key={item.path}
                onClick={() => handleNavClick(item.path)}
                className={`w-full text-left px-4 py-3 rounded-lg font-medium flex items-center gap-3 transition-all ${isActive
                  ? "bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400 shadow-sm"
                  : "text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700"
                  }`}
              >
                <Icon size={18} /> {item.label}
              </button>
            );
          })}
        </nav>
        <div className="p-4 border-t border-gray-100 dark:border-gray-700 flex flex-col gap-3">
          <div className="flex items-center gap-3 px-2">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold border border-blue-50 dark:border-blue-800">
              {initials}
            </div>
            <div className="flex-1 overflow-hidden">
              <p className="text-sm font-bold text-gray-700 dark:text-gray-200 truncate">{userName}</p>
              <p className="text-xs text-gray-400 dark:text-gray-500">{hasClass ? (userInfo.className || '已加入班级') : '未加入班级'}</p>
            </div>
          </div>
          {!hasClass && (
            <button
              type="button"
              onClick={openJoinClassModal}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-bold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-xl transition-all border border-blue-200 dark:border-blue-800"
            >
              <School size={18} /> 加入班级
            </button>
          )}
          <button
            onClick={() => setIsPasswordModalOpen(true)}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-bold text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-xl transition-all border border-gray-200 dark:border-gray-700 shadow-sm"
          >
            <Key size={18} /> 修改密码
          </button>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-bold text-red-600 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/40 rounded-xl transition-all border border-red-100 dark:border-red-900/30 shadow-sm"
          >
            <LogOut size={18} /> 退出登录
          </button>
        </div>
      </div>

      {/* 右侧内容区 */}
      <div className="flex-1 flex flex-col overflow-hidden pt-16 md:pt-0">{children}</div>

      {/* 修改密码弹窗 */}
      <PasswordChangeModal
        isOpen={isPasswordModalOpen}
        onClose={() => setIsPasswordModalOpen(false)}
      />

      {/* 加入班级弹窗 */}
      {showJoinClassModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={() => !joinClassLoading && setShowJoinClassModal(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">加入班级</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">选择要加入的班级后，即可使用任务中心等需关联班级的功能。</p>
            {joinClassError && <p className="text-sm text-red-600 dark:text-red-400 mb-3">{joinClassError}</p>}
            <form onSubmit={handleJoinClass}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">选择班级</label>
                <select name="class_id" required className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-gray-100 text-sm">
                  <option value="">请选择</option>
                  {classList.map(c => (
                    <option key={c.id} value={c.id}>{c.class_name}（{c.class_code}）{c.grade ? ` · ${c.grade}` : ''}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-2">
                <button type="button" onClick={() => !joinClassLoading && setShowJoinClassModal(false)} className="flex-1 py-2 rounded-lg border border-gray-200 dark:border-white/10 text-gray-700 dark:text-gray-300 text-sm font-medium">取消</button>
                <button type="submit" disabled={joinClassLoading || classList.length === 0} className="flex-1 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium disabled:opacity-50">{joinClassLoading ? '提交中…' : '确认加入'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentLayout;
