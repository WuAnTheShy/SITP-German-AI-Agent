import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

const ThemeToggle = () => {
    const { theme, toggleTheme } = useTheme();

    return (
        <button
            onClick={toggleTheme}
            className="fixed bottom-6 right-6 p-3 rounded-full shadow-lg z-50 
                       bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 
                       border border-gray-200 dark:border-gray-700 
                       hover:scale-110 transition-transform flex items-center justify-center"
            title={theme === 'dark' ? '切换浅色模式' : '切换深色模式'}
        >
            {theme === 'dark' ? <Sun size={24} className="text-yellow-400" /> : <Moon size={24} className="text-indigo-600" />}
        </button>
    );
};

export default ThemeToggle;
