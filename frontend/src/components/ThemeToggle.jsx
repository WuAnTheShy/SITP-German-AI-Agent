import React, { useState, useEffect, useRef } from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

const ThemeToggle = () => {
    const { theme, toggleTheme } = useTheme();
    // 默认位置：右下角
    const [position, setPosition] = useState({ x: window.innerWidth - 80, y: window.innerHeight - 80 });
    const [isDragging, setIsDragging] = useState(false);
    const [isPressed, setIsPressed] = useState(false);
    const dragStartPos = useRef({ x: 0, y: 0 });
    const mouseStartPos = useRef({ x: 0, y: 0 });
    const buttonRef = useRef(null);
    const hasDragged = useRef(false);
    const DRAG_THRESHOLD = 5; // 5px 阈值

    // 初始化：从本地存储读取位置
    useEffect(() => {
        const savedPos = localStorage.getItem('theme-toggle-pos');
        if (savedPos) {
            try {
                const parsed = JSON.parse(savedPos);
                // 确保位置在当前视口内
                const x = Math.min(Math.max(20, parsed.x), window.innerWidth - 60);
                const y = Math.min(Math.max(20, parsed.y), window.innerHeight - 60);
                setPosition({ x, y });
            } catch (e) {
                console.error('Failed to parse saved position', e);
            }
        }

        // 监听窗口大小变化
        const handleResize = () => {
            setPosition(prev => ({
                x: Math.min(prev.x, window.innerWidth - 60),
                y: Math.min(prev.y, window.innerHeight - 60)
            }));
        };
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const handleStart = (clientX, clientY) => {
        setIsPressed(true);
        mouseStartPos.current = { x: clientX, y: clientY };
        dragStartPos.current = {
            x: clientX - position.x,
            y: clientY - position.y
        };
        hasDragged.current = false;
    };

    const handleMove = (clientX, clientY) => {
        if (!isPressed) return;

        // 如果还没开始拖拽，检查是否超过阈值
        if (!isDragging) {
            const distance = Math.sqrt(
                Math.pow(clientX - mouseStartPos.current.x, 2) +
                Math.pow(clientY - mouseStartPos.current.y, 2)
            );
            if (distance > DRAG_THRESHOLD) {
                setIsDragging(true);
            } else {
                return;
            }
        }

        hasDragged.current = true;

        let newX = clientX - dragStartPos.current.x;
        let newY = clientY - dragStartPos.current.y;

        // 边界限制
        newX = Math.min(Math.max(10, newX), window.innerWidth - 60);
        newY = Math.min(Math.max(10, newY), window.innerHeight - 60);

        setPosition({ x: newX, y: newY });
    };

    const handleEnd = () => {
        if (isPressed) {
            setIsPressed(false);
            if (isDragging) {
                setIsDragging(false);
                localStorage.setItem('theme-toggle-pos', JSON.stringify(position));
            }
        }
    };

    // 鼠标事件
    const onMouseDown = (e) => handleStart(e.clientX, e.clientY);

    // 触摸事件
    const onTouchStart = (e) => {
        const touch = e.touches[0];
        handleStart(touch.clientX, touch.clientY);
    };

    useEffect(() => {
        const onMouseMove = (e) => handleMove(e.clientX, e.clientY);
        const onTouchMove = (e) => {
            if (isPressed) {
                if (isDragging) {
                    e.preventDefault(); // 只有在真正拖拽时才防止滚动
                }
                const touch = e.touches[0];
                handleMove(touch.clientX, touch.clientY);
            }
        };

        if (isPressed) {
            window.addEventListener('mousemove', onMouseMove);
            window.addEventListener('mouseup', handleEnd);
            window.addEventListener('touchmove', onTouchMove, { passive: false });
            window.addEventListener('touchend', handleEnd);
        }

        return () => {
            window.removeEventListener('mousemove', onMouseMove);
            window.removeEventListener('mouseup', handleEnd);
            window.removeEventListener('touchmove', onTouchMove);
            window.removeEventListener('touchend', handleEnd);
        };
    }, [isPressed, isDragging, position]);

    const handleClick = (e) => {
        // 如果发生了明显的位移，则不触发点击切换主题
        if (hasDragged.current) {
            e.preventDefault();
            e.stopPropagation();
        } else {
            toggleTheme();
        }
    };

    return (
        <button
            ref={buttonRef}
            onMouseDown={onMouseDown}
            onTouchStart={onTouchStart}
            onClick={handleClick}
            style={{
                left: `${position.x}px`,
                top: `${position.y}px`,
                touchAction: 'none' // 禁用浏览器默认触摸行为
            }}
            className={`fixed p-3 rounded-full shadow-2xl z-[9999] 
                       bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 
                       border border-gray-200 dark:border-gray-700 
                       transition-transform duration-75 flex items-center justify-center
                       ${isDragging ? 'scale-110 cursor-grabbing' : 'hover:scale-110 cursor-grab active:scale-95'}`}
            title={theme === 'dark' ? '切换浅色模式' : '切换深色模式'}
        >
            {theme === 'dark' ? <Sun size={24} className="text-yellow-400 pointer-events-none" /> : <Moon size={24} className="text-indigo-600 pointer-events-none" />}
        </button>
    );
};

export default ThemeToggle;
