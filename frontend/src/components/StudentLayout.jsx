import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Bot, MessageSquare, ScrollText, Headphones,
  BookMarked, PenLine, BarChart3, BookX, Star
} from 'lucide-react';

const navItems = [
  { label: '智能对话', icon: Bot, path: '/student/home' },
  { label: '场景对话', icon: MessageSquare, path: '/student/ai-scene-chat' },
  { label: '语法练习', icon: ScrollText, path: '/student/grammar-practice' },
  { label: '听说训练', icon: Headphones, path: '/student/listening-speaking' },
  { label: '词汇学习', icon: BookMarked, path: '/student/vocab-learning' },
  { label: '写作助手', icon: PenLine, path: '/student/writing-assistant' },
  { label: '学习进度', icon: BarChart3, path: '/student/learning-progress' },
  { label: '错题本复习', icon: BookX, path: '/student/error-book' },
  { label: '我的收藏', icon: Star, path: '/student/favorites' },
];

const StudentLayout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="flex h-screen bg-gray-50">
      {/* 左侧导航栏 */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col shrink-0">
        <div className="p-6 border-b border-gray-100">
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
                className={`w-full text-left px-4 py-3 rounded-lg font-medium flex items-center gap-3 transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Icon size={18} /> {item.label}
              </button>
            );
          })}
        </nav>
        <div className="p-4 border-t border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold">
              WS
            </div>
            <div>
              <p className="text-sm font-bold text-gray-700">魏同学</p>
              <p className="text-xs text-gray-400">在线</p>
            </div>
          </div>
        </div>
      </div>

      {/* 右侧内容区 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {children}
      </div>
    </div>
  );
};

export default StudentLayout;
