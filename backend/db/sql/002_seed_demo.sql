-- SITP German AI Agent
-- Demo seed data for local development

BEGIN;

-- 用户
INSERT INTO users (username, password_hash, role, display_name)
VALUES
    ('t_zhang', 'demo_hash_teacher', 'teacher', '张老师'),
    ('s_li',    'demo_hash_student', 'student', '李娜'),
    ('s_wang',  'demo_hash_student', 'student', '王强')
ON CONFLICT (username) DO NOTHING;

-- 班级
INSERT INTO classes (class_code, class_name, grade, teacher_user_id)
VALUES (
    'SE-2026-4',
    '软件工程(四)班',
    '2026',
    (SELECT id FROM users WHERE username = 't_zhang')
)
ON CONFLICT (class_code) DO NOTHING;

-- 学生
INSERT INTO students (uid, user_id, class_id, name, active_score, overall_score, weak_point)
VALUES
(
    '2452001',
    (SELECT id FROM users WHERE username = 's_li'),
    (SELECT id FROM classes WHERE class_code = 'SE-2026-4'),
    '李娜',
    88,
    91.5,
    '虚拟式'
),
(
    '2452002',
    (SELECT id FROM users WHERE username = 's_wang'),
    (SELECT id FROM classes WHERE class_code = 'SE-2026-4'),
    '王强',
    64,
    78.0,
    '被动语态'
)
ON CONFLICT (uid) DO NOTHING;

-- 能力画像
INSERT INTO student_abilities (student_id, listening, speaking, reading, writing, ai_diagnosis)
VALUES
(
    (SELECT id FROM students WHERE uid = '2452001'),
    89, 86, 92, 90,
    '在虚拟式和复杂从句中仍有少量错误，建议继续强化。'
),
(
    (SELECT id FROM students WHERE uid = '2452002'),
    68, 62, 75, 70,
    '被动语态掌握不足，建议优先完成专项练习。'
)
ON CONFLICT (student_id) DO NOTHING;

-- 作业
INSERT INTO homeworks (
    student_id, title, status, submitted_at, score,
    file_type, file_url, file_name, file_size, ai_comment
)
VALUES
(
    (SELECT id FROM students WHERE uid = '2452001'),
    '德语写作作业-第3周',
    '已完成',
    NOW() - INTERVAL '2 day',
    92,
    'text',
    'https://example.com/homeworks/ln-week3.txt',
    'ln-week3.txt',
    '24 KB',
    '结构清晰，语法整体正确，个别搭配可优化。'
),
(
    (SELECT id FROM students WHERE uid = '2452002'),
    '德语口语录音-餐厅场景',
    '待订正',
    NOW() - INTERVAL '1 day',
    76,
    'audio',
    'https://example.com/homeworks/wq-restaurant.mp3',
    'wq-restaurant.mp3',
    '2.4 MB',
    '发音较自然，但时态使用有明显问题。'
);

COMMIT;
