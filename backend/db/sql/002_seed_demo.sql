-- SITP German AI Agent
-- Demo seed data for local development

BEGIN;

-- 用户
INSERT INTO users (username, password_hash, role, display_name)
VALUES
    ('t_zhang', md5(random()::text || clock_timestamp()::text || 't_zhang'), 'teacher', '张老师'),
    ('t_liu',   md5(random()::text || clock_timestamp()::text || 't_liu'),   'teacher', '刘老师'),
    ('t_chen',  md5(random()::text || clock_timestamp()::text || 't_chen'),  'teacher', '陈老师'),
    ('s_li',    md5(random()::text || clock_timestamp()::text || 's_li'),    'student', '李娜'),
    ('s_wang',  md5(random()::text || clock_timestamp()::text || 's_wang'),  'student', '王强'),
    ('s_zhao',  md5(random()::text || clock_timestamp()::text || 's_zhao'),  'student', '赵敏'),
    ('s_sun',   md5(random()::text || clock_timestamp()::text || 's_sun'),   'student', '孙浩'),
    ('s_qian',  md5(random()::text || clock_timestamp()::text || 's_qian'),  'student', '钱雨'),
    ('s_he',    md5(random()::text || clock_timestamp()::text || 's_he'),    'student', '何宁')
ON CONFLICT (username) DO NOTHING;

-- 班级
INSERT INTO classes (class_code, class_name, grade, teacher_user_id)
VALUES
(
    'SE-2026-4',
    '软件工程(四)班',
    '2026',
    (SELECT id FROM users WHERE username = 't_zhang')
),
(
    'DS-2026-1',
    '数据科学(一)班',
    '2026',
    (SELECT id FROM users WHERE username = 't_liu')
),
(
    'FA-2025-2',
    '德语强化(二)班',
    '2025',
    (SELECT id FROM users WHERE username = 't_chen')
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
),
(
    '2452003',
    (SELECT id FROM users WHERE username = 's_zhao'),
    (SELECT id FROM classes WHERE class_code = 'DS-2026-1'),
    '赵敏',
    72,
    82.5,
    '名词格变化'
),
(
    '2452004',
    (SELECT id FROM users WHERE username = 's_sun'),
    (SELECT id FROM classes WHERE class_code = 'DS-2026-1'),
    '孙浩',
    59,
    71.0,
    '词序'
),
(
    '2452005',
    (SELECT id FROM users WHERE username = 's_qian'),
    (SELECT id FROM classes WHERE class_code = 'FA-2025-2'),
    '钱雨',
    85,
    89.0,
    '介词搭配'
),
(
    '2452006',
    (SELECT id FROM users WHERE username = 's_he'),
    (SELECT id FROM classes WHERE class_code = 'FA-2025-2'),
    '何宁',
    67,
    76.5,
    '虚拟式'
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
),
(
    (SELECT id FROM students WHERE uid = '2452003'),
    74, 70, 85, 81,
    '名词格变化细节仍需巩固，建议加强第四格与第三格对比。'
),
(
    (SELECT id FROM students WHERE uid = '2452004'),
    61, 58, 73, 69,
    '句子词序错误较多，建议先练主从句语序规则。'
),
(
    (SELECT id FROM students WHERE uid = '2452005'),
    86, 84, 90, 88,
    '整体表现较好，介词固定搭配可进一步提升。'
),
(
    (SELECT id FROM students WHERE uid = '2452006'),
    69, 65, 77, 74,
    '虚拟式表达不稳定，建议增加情景造句训练。'
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
