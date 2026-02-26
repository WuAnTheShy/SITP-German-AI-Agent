-- ============================================================
-- SITP German AI Agent
-- 学生端演示种子数据
-- 依赖: 001_init_schema.sql, 002_seed_demo.sql, 003_student_schema.sql
-- ============================================================

BEGIN;

-- ============================================================
-- A. 对话场景字典 (前端 AISceneChat.jsx 硬编码的 4 个场景)
-- ============================================================
INSERT INTO chat_scenes (name, description) VALUES
    ('校园课堂问答', '和老师互动、回答课堂问题'),
    ('日常购物交流', '超市/商店买东西的德语对话'),
    ('留学面试沟通', '德国大学入学面试常见问题'),
    ('餐厅点餐对话', '德国餐厅点餐、询问菜品')
ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- B. 词汇库 (A1 日常通用，20 条基础词汇)
-- ============================================================
INSERT INTO vocabularies (german, chinese, example, level, topic) VALUES
    ('Hallo',            '你好',             'Hallo, wie geht es Ihnen?',                     'A1', '日常通用'),
    ('Danke',            '谢谢',             'Danke schön für Ihre Hilfe.',                    'A1', '日常通用'),
    ('Bitte',            '请/不客气',        'Bitte schön, nehmen Sie Platz.',                 'A1', '日常通用'),
    ('Ja',               '是',               'Ja, das stimmt.',                                'A1', '日常通用'),
    ('Nein',             '不',               'Nein, das ist falsch.',                          'A1', '日常通用'),
    ('Guten Morgen',     '早上好',           'Guten Morgen, Herr Müller!',                     'A1', '日常通用'),
    ('Guten Tag',        '你好(白天)',        'Guten Tag! Kann ich Ihnen helfen?',              'A1', '日常通用'),
    ('Auf Wiedersehen',  '再见',             'Auf Wiedersehen und schönen Tag!',               'A1', '日常通用'),
    ('Entschuldigung',   '对不起/打扰一下',  'Entschuldigung, wo ist der Bahnhof?',            'A1', '日常通用'),
    ('Wasser',           '水',               'Ich möchte ein Glas Wasser, bitte.',             'A1', '日常通用'),
    ('Brot',             '面包',             'Das Brot schmeckt sehr gut.',                    'A1', '日常通用'),
    ('Milch',            '牛奶',             'Ich trinke gern Milch zum Frühstück.',           'A1', '日常通用'),
    ('Kaffee',           '咖啡',             'Einen Kaffee mit Zucker, bitte.',                'A1', '日常通用'),
    ('Schule',           '学校',             'Die Schule beginnt um acht Uhr.',                'A1', '日常通用'),
    ('Buch',             '书',               'Ich lese ein interessantes Buch.',               'A1', '日常通用'),
    ('Freund',           '朋友',             'Mein Freund kommt aus China.',                   'A1', '日常通用'),
    ('Familie',          '家庭',             'Meine Familie wohnt in Shanghai.',               'A1', '日常通用'),
    ('Haus',             '房子',             'Das Haus ist sehr groß.',                        'A1', '日常通用'),
    ('Auto',             '汽车',             'Ich fahre mit dem Auto zur Arbeit.',             'A1', '日常通用'),
    ('Zeit',             '时间',             'Haben Sie Zeit für einen Kaffee?',               'A1', '日常通用')
ON CONFLICT (german, level) DO NOTHING;

-- ============================================================
-- C. 语法分类 & 练习题
-- ============================================================

-- C1. 分类
INSERT INTO grammar_categories (name, description) VALUES
    ('动词变位 (Konjugation)',   '德语动词在不同人称和时态下的词形变化'),
    ('名词性/格 (Deklination)',  '德语名词的阴阳中性及四个格的变化规则'),
    ('现在完成时 (Perfekt)',     '表达过去发生的事情，由 haben/sein + 过去分词构成'),
    ('被动语态 (Passiv)',        '用 werden + 过去分词构成的被动表达'),
    ('虚拟式 (Konjunktiv II)',   '表达非现实愿望、委婉请求等')
ON CONFLICT (name) DO NOTHING;

-- C2. 练习题 — 动词变位
INSERT INTO grammar_exercises (category_id, question, correct_answer, analysis)
SELECT c.id, q.question, q.answer, q.analysis
FROM grammar_categories c,
     (VALUES
         ('Ich ___ (sein) Student.',          'bin',    'sein 的第一人称单数变位是 bin：ich bin, du bist, er/sie/es ist.'),
         ('Du ___ (haben) ein Buch.',          'hast',   'haben 的第二人称单数变位是 hast：ich habe, du hast, er/sie/es hat.'),
         ('Er ___ (gehen) zur Schule.',        'geht',   'gehen 的第三人称单数变位是 geht：ich gehe, du gehst, er geht.'),
         ('Wir ___ (lernen) Deutsch.',         'lernen', 'lernen 的第一人称复数变位与不定式相同：wir lernen, ihr lernt, sie lernen.')
     ) AS q(question, answer, analysis)
WHERE c.name = '动词变位 (Konjugation)';

-- C3. 练习题 — 名词性/格
INSERT INTO grammar_exercises (category_id, question, correct_answer, analysis)
SELECT c.id, q.question, q.answer, q.analysis
FROM grammar_categories c,
     (VALUES
         ('Das ist ___ (ein) Tisch. (阳性主格)',                    'ein',  '阳性名词主格不定冠词为 ein：ein Tisch (桌子).'),
         ('Ich sehe ___ (der) Mann. (阳性第四格)',                  'den',  '阳性名词第四格定冠词 der→den：Ich sehe den Mann.'),
         ('Er gibt ___ (die) Frau ein Geschenk. (阴性第三格)',       'der',  '阴性名词第三格定冠词 die→der：Er gibt der Frau ein Geschenk.'),
         ('Das Auto ___ (das) Kindes ist neu. (中性第二格)',         'des',  '中性名词第二格定冠词 das→des：das Auto des Kindes.')
     ) AS q(question, answer, analysis)
WHERE c.name = '名词性/格 (Deklination)';

-- C4. 练习题 — 现在完成时
INSERT INTO grammar_exercises (category_id, question, correct_answer, analysis)
SELECT c.id, q.question, q.answer, q.analysis
FROM grammar_categories c,
     (VALUES
         ('Ich ___ gestern ins Kino gegangen. (sein/haben)',   'bin',  'gehen 是移动动词，完成时用 sein 作助动词：Ich bin gegangen.'),
         ('Sie ___ ein Buch gelesen. (sein/haben)',            'hat',  'lesen 是及物动词，完成时用 haben 作助动词：Sie hat gelesen.'),
         ('Wir ___ nach Berlin gefahren. (sein/haben)',        'sind', 'fahren 表位移时用 sein：Wir sind nach Berlin gefahren.')
     ) AS q(question, answer, analysis)
WHERE c.name = '现在完成时 (Perfekt)';

-- C5. 练习题 — 被动语态
INSERT INTO grammar_exercises (category_id, question, correct_answer, analysis)
SELECT c.id, q.question, q.answer, q.analysis
FROM grammar_categories c,
     (VALUES
         ('Das Buch ___ von mir gelesen. (werden)',     'wird',   '现在时被动：werden + 过去分词。Das Buch wird gelesen.'),
         ('Die Tür ___ geschlossen. (werden-过去时)',    'wurde',  '过去时被动：wurden + 过去分词。Die Tür wurde geschlossen.'),
         ('Der Brief ist ___ worden. (schreiben)',       'geschrieben', '完成时被动：sein + 过去分词 + worden。Der Brief ist geschrieben worden.')
     ) AS q(question, answer, analysis)
WHERE c.name = '被动语态 (Passiv)';

-- C6. 练习题 — 虚拟式
INSERT INTO grammar_exercises (category_id, question, correct_answer, analysis)
SELECT c.id, q.question, q.answer, q.analysis
FROM grammar_categories c,
     (VALUES
         ('Wenn ich reich ___, würde ich reisen. (sein)',     'wäre',   'Konjunktiv II von sein: ich wäre, du wärst, er wäre.'),
         ('Ich ___ gern einen Kaffee. (haben)',               'hätte',  'Konjunktiv II von haben: ich hätte, du hättest, er hätte.'),
         ('___ Sie mir bitte helfen? (können)',                'Könnten', 'Konjunktiv II von können: Könnten Sie...? 表委婉请求.')
     ) AS q(question, answer, analysis)
WHERE c.name = '虚拟式 (Konjunktiv II)';

-- ============================================================
-- D. 听力材料 (4 条)
-- ============================================================
INSERT INTO listening_materials (title, level, duration, audio_url, script) VALUES
    ('Begrüßungen im Alltag',
     'A1', '2:30',
     'https://example.com/audio/begruessungen.mp3',
     'Hallo! Guten Morgen! Wie geht es Ihnen? — Mir geht es gut, danke. Und Ihnen? — Auch gut, danke der Nachfrage. Auf Wiedersehen!'),
    ('Im Restaurant bestellen',
     'A1', '3:15',
     'https://example.com/audio/restaurant.mp3',
     'Guten Tag! Ich hätte gern eine Suppe und ein Glas Wasser, bitte. — Möchten Sie auch etwas zu trinken? — Ja, einen Kaffee bitte. — Das macht zusammen 8 Euro 50.'),
    ('Am Bahnhof',
     'A2', '4:00',
     'https://example.com/audio/bahnhof.mp3',
     'Entschuldigung, wann fährt der nächste Zug nach München? — Der Zug fährt um 14 Uhr 30 von Gleis 5. — Muss ich umsteigen? — Nein, es ist eine Direktverbindung.'),
    ('Beim Arzt',
     'A2', '3:45',
     'https://example.com/audio/arzt.mp3',
     'Was kann ich für Sie tun? — Ich habe Kopfschmerzen und Fieber seit gestern Abend. — Haben Sie auch Halsschmerzen? — Ja, ein bisschen. — Ich verschreibe Ihnen ein Medikament.')
ON CONFLICT (title) DO NOTHING;

-- ============================================================
-- E. 错题分类字典
-- ============================================================
INSERT INTO error_book_categories (name) VALUES
    ('动词变位'),
    ('名词格变化'),
    ('句序错误'),
    ('介词搭配'),
    ('时态错误')
ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- F. 收藏分类字典
-- ============================================================
INSERT INTO favorite_categories (type, name) VALUES
    ('vocab',    '词汇'),
    ('grammar',  '语法规则'),
    ('sentence', '好句摘录'),
    ('note',     '学习笔记')
ON CONFLICT (type) DO NOTHING;

-- ============================================================
-- G. 为演示学生生成学习进度 & 知识点 & 错题 & 收藏
--    (依赖 002_seed_demo.sql 中 uid='2452001' 的李娜)
-- ============================================================

-- G1. 学习时长记录
INSERT INTO learning_sessions (student_id, module, duration_minutes, content, session_date)
SELECT s.id, ls.module, ls.dur, ls.content, ls.d
FROM students s,
     (VALUES
         ('词汇学习',   45, '学习 A1 日常通用词汇',     CURRENT_DATE - 6),
         ('语法练习',   30, '动词变位专项练习',           CURRENT_DATE - 5),
         ('情景对话',   60, '校园课堂问答场景训练',       CURRENT_DATE - 4),
         ('听说训练',   25, '听力材料: Begrüßungen',    CURRENT_DATE - 3),
         ('写作辅助',   40, '德语短文语法检查',           CURRENT_DATE - 2),
         ('语法练习',   35, '名词性/格练习',             CURRENT_DATE - 1),
         ('情景对话',   50, '餐厅点餐对话训练',           CURRENT_DATE)
     ) AS ls(module, dur, content, d)
WHERE s.uid = '2452001';

-- G2. 知识点掌握度
INSERT INTO student_knowledge_mastery (student_id, knowledge_name, mastery_level)
SELECT s.id, km.kn, km.lv
FROM students s,
     (VALUES
         ('基础问候语',    '熟练'),
         ('动词 sein/haben 变位', '熟练'),
         ('第四格用法',    '一般'),
         ('现在完成时',    '一般'),
         ('被动语态',      '薄弱'),
         ('虚拟式',        '薄弱')
     ) AS km(kn, lv)
WHERE s.uid = '2452001'
ON CONFLICT (student_id, knowledge_name) DO NOTHING;

-- G3. 错题记录
INSERT INTO error_book_entries (student_id, category_id, source, question, user_answer, correct_answer, analysis)
SELECT s.id, ec.id, eb.source, eb.question, eb.user_ans, eb.correct_ans, eb.analysis
FROM students s
CROSS JOIN (VALUES
    ('动词变位', '语法练习', 'Er ___ (gehen) zur Schule.',
     'gehet', 'geht', 'gehen 第三人称单数变位去 -en 加 -t：er geht.'),
    ('时态错误', '语法练习', 'Ich ___ gestern ins Kino gegangen. (sein/haben)',
     'habe', 'bin', 'gehen 是位移动词，完成时必须用 sein 作助动词.'),
    ('名词格变化', '语法练习', 'Ich sehe ___ (der) Mann. (阳性第四格)',
     'der', 'den', '阳性名词第四格定冠词 der 需变位为 den.')
) AS eb(cat_name, source, question, user_ans, correct_ans, analysis)
JOIN error_book_categories ec ON ec.name = eb.cat_name
WHERE s.uid = '2452001';

-- G4. 收藏记录
INSERT INTO favorites (student_id, category_id, content, translate, rule, note)
SELECT s.id, fc.id, fv.content, fv.translate, fv.rule, fv.note
FROM students s
CROSS JOIN (VALUES
    ('vocab',    'Entschuldigung',                '对不起/打扰一下',  NULL,                           '最实用的德语日常词汇之一'),
    ('grammar',  '阳性第四格变化规则',              NULL,              'der→den, ein→einen, 其他不变',  '这个容易忘记'),
    ('sentence', 'Ich hätte gern einen Kaffee.',   '我想要一杯咖啡。', NULL,                           '虚拟式的经典用法'),
    ('note',     '德语名词首字母必须大写',           NULL,              NULL,                           '德语和英语不同的重要规则')
) AS fv(cat_type, content, translate, rule, note)
JOIN favorite_categories fc ON fc.type = fv.cat_type
WHERE s.uid = '2452001';

COMMIT;
