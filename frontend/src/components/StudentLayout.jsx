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
} from "lucide-react";

const StudentLayout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  // 从 localStorage 获取实际登录用户信息
  const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
  const userId = userInfo.id || userInfo.studentId || '';
  const userName = userInfo.name || '未登录';
  const initials = userName.slice(0, 1);

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userInfo');
    navigate('/');
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

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* 左侧导航栏 */}
      <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col shrink-0">
        <div className="p-6 border-b border-gray-100 dark:border-gray-700">
          <h2 className="text-xl font-bold text-blue-900 flex items-center gap-2">
            <Bot size={24} /> AI-Tutor
          </h2>
        </div>
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`w-full text-left px-4 py-3 rounded-lg font-medium flex items-center gap-3 transition-colors ${isActive
                  ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400"
                  : "text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:bg-gray-900"
                  }`}
              >
                <Icon size={18} /> {item.label}
              </button>
            );
          })}
        </nav>
        <div className="p-4 border-t border-gray-100 dark:border-gray-700 flex flex-col gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold">
              {initials}
            </div>
            <div className="flex-1 overflow-hidden">
              <p className="text-sm font-bold text-gray-700 dark:text-gray-300 truncate">{userName}</p>
              <p className="text-xs text-gray-400 dark:text-gray-500">在线活跃中</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-bold text-red-600 bg-red-50 dark:bg-red-900/30 hover:bg-red-100 rounded-xl transition-all border border-red-100 shadow-sm dark:shadow-gray-900/50"
          >
            <LogOut size={18} /> 退出登录
          </button>
        </div>
      </div>

      {/* 右侧内容区 */}
      <div className="flex-1 flex flex-col overflow-hidden">{children}</div>
    </div>
  );
};

export default StudentLayout;
