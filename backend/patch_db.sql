-- 试卷表增加题目内容存储字段
ALTER TABLE exams ADD COLUMN content JSONB DEFAULT '[]'::jsonb NOT NULL;
