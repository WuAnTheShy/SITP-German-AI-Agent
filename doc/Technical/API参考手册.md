# SITP German AI Agent API 参考手册

> 建议先在运行环境中打开 Swagger 文档核对字段细节：  
> http://localhost:9000/docs（Docker）或 http://localhost:8000/docs（本地后端）

---

## 1. 通用说明

- 大部分接口前缀为 /api。
- 认证方式：Authorization: Bearer token。
- 返回结构通常为 code/message/data。
- 账号相关接口区分管理员、教师、学生角色权限。

---

## 2. 认证与账号

| 方法 | 路径                       | 说明                         |
| ---- | -------------------------- | ---------------------------- |
| POST | /api/auth/login            | 统一登录（学生/教师/管理员） |
| POST | /api/auth/student-register | 学生注册                     |
| POST | /api/auth/teacher-register | 教师注册                     |
| PUT  | /api/user/password         | 当前登录用户修改密码         |

---

## 3. 管理员接口（前缀 /api/admin）

### 3.1 教师管理

| 方法   | 路径                          | 说明              |
| ------ | ----------------------------- | ----------------- |
| GET    | /api/admin/teachers           | 查询教师列表      |
| PUT    | /api/admin/teachers/{user_id} | 更新教师信息/状态 |
| DELETE | /api/admin/teachers/{user_id} | 删除教师          |

### 3.2 学生管理

| 方法   | 路径                             | 说明         |
| ------ | -------------------------------- | ------------ |
| GET    | /api/admin/students              | 查询学生列表 |
| PUT    | /api/admin/students/{student_id} | 更新学生信息 |
| DELETE | /api/admin/students/{student_id} | 删除学生     |

### 3.3 班级管理

| 方法   | 路径                          | 说明         |
| ------ | ----------------------------- | ------------ |
| GET    | /api/admin/classes            | 查询班级列表 |
| POST   | /api/admin/classes            | 创建班级     |
| PUT    | /api/admin/classes/{class_id} | 修改班级     |
| DELETE | /api/admin/classes/{class_id} | 删除班级     |

### 3.4 系统设置与审核

| 方法 | 路径                                        | 说明               |
| ---- | ------------------------------------------- | ------------------ |
| GET  | /api/admin/system/settings                  | 查询系统设置       |
| PUT  | /api/admin/system/settings                  | 更新系统设置       |
| GET  | /api/admin/users/pending-teachers           | 待审核教师列表     |
| PUT  | /api/admin/users/teachers/{user_id}/approve | 通过教师审核       |
| PUT  | /api/admin/users/teachers/{user_id}/reject  | 拒绝教师审核       |
| PUT  | /api/admin/users/{user_id}/password         | 管理员重置用户密码 |

### 3.5 知识库管理

| 方法   | 路径                           | 说明               |
| ------ | ------------------------------ | ------------------ |
| GET    | /api/admin/kb/docs             | 公共知识库文档列表 |
| POST   | /api/admin/kb/upload           | 上传公共知识库文档 |
| POST   | /api/admin/kb/reindex/{doc_id} | 重新索引公共文档   |
| DELETE | /api/admin/kb/docs/{doc_id}    | 删除公共文档       |

### 3.6 可观测性（Trace）

| 方法 | 路径                            | 说明         |
| ---- | ------------------------------- | ------------ |
| GET  | /api/admin/traces               | Trace 列表   |
| GET  | /api/admin/traces/{trace_id}    | Trace 详情   |
| GET  | /api/admin/traces/stats/by_tool | 工具调用统计 |

---

## 4. 教师业务接口

| 方法   | 路径                                       | 说明           |
| ------ | ------------------------------------------ | -------------- |
| GET    | /api/teacher/dashboard                     | 教师仪表盘数据 |
| POST   | /api/scenario/publish                      | 发布情景任务   |
| POST   | /api/exam/generate                         | 生成并发布试卷 |
| GET    | /api/teacher/scenario/list                 | 情景发布历史   |
| GET    | /api/teacher/exam/list                     | 试卷列表       |
| GET    | /api/teacher/exam/{exam_id}                | 试卷详情       |
| GET    | /api/teacher/pending-students              | 待审核学生列表 |
| GET    | /api/teacher/students                      | 班级学生列表   |
| PUT    | /api/teacher/students/{student_id}         | 更新学生信息   |
| DELETE | /api/teacher/students/{student_id}         | 删除学生       |
| PUT    | /api/teacher/students/{student_id}/approve | 通过学生审核   |
| PUT    | /api/teacher/students/{student_id}/reject  | 拒绝学生审核   |

---

## 5. 教师端作业与学生详情

| 方法 | 路径                        | 说明               |
| ---- | --------------------------- | ------------------ |
| GET  | /api/student/detail         | 学生详情画像       |
| GET  | /api/homework/detail        | 作业详情           |
| GET  | /api/homework/download/{id} | 下载作业/答卷      |
| POST | /api/homework/save          | 保存批改结果       |
| POST | /api/student/push-scheme    | 推送个性化学习方案 |

---

## 6. 学生任务与考试

| 方法 | 路径                                         | 说明             |
| ---- | -------------------------------------------- | ---------------- |
| GET  | /api/student/classes                         | 可加入班级列表   |
| POST | /api/student/join-class                      | 学生加入班级     |
| GET  | /api/student/tasks                           | 任务列表         |
| GET  | /api/student/exam/assignment/{assignment_id} | 试卷作答页数据   |
| POST | /api/student/exam/submit                     | 提交试卷         |
| GET  | /api/student/exam/result/{assignment_id}     | 试卷结果         |
| POST | /api/student/task/complete                   | 手动完成任务打点 |

---

## 7. 学生学习工具

### 7.1 词汇

| 方法 | 路径                        | 说明        |
| ---- | --------------------------- | ----------- |
| GET  | /api/student/vocab/list     | 词汇列表    |
| POST | /api/student/vocab/collect  | 收藏词汇    |
| POST | /api/student/vocab/generate | AI 词汇生成 |

### 7.2 语法

| 方法 | 路径                            | 说明         |
| ---- | ------------------------------- | ------------ |
| GET  | /api/student/grammar/categories | 语法分类     |
| GET  | /api/student/grammar/exercises  | 语法练习题   |
| POST | /api/student/grammar/submit     | 提交语法练习 |
| POST | /api/student/grammar/generate   | 生成语法练习 |

### 7.3 听说写

| 方法 | 路径                                   | 说明         |
| ---- | -------------------------------------- | ------------ |
| GET  | /api/student/listening/materials       | 听力素材列表 |
| GET  | /api/student/listening/material/detail | 听力素材详情 |
| POST | /api/student/speaking/evaluate         | 口语评估     |
| POST | /api/student/writing/check             | 写作纠错     |
| POST | /api/student/writing/generate-sample   | AI 范文生成  |

### 7.4 错题本与收藏夹

| 方法   | 路径                                      | 说明             |
| ------ | ----------------------------------------- | ---------------- |
| GET    | /api/student/error-book/categories        | 错题分类         |
| GET    | /api/student/error-book/list              | 错题列表         |
| POST   | /api/student/error-book/start-review      | 开始错题复习     |
| POST   | /api/student/error-book/mark-mastered     | 标记已掌握       |
| DELETE | /api/student/error-book/delete/{error_id} | 删除错题         |
| GET    | /api/student/favorites/categories         | 收藏分类         |
| GET    | /api/student/favorites/list               | 收藏列表         |
| POST   | /api/student/favorites/add                | 新增收藏         |
| DELETE | /api/student/favorites/{fav_id}           | 删除收藏         |
| POST   | /api/student/favorites/ai-extend          | 收藏扩展学习建议 |
| GET    | /api/student/learning/progress            | 学习进度总览     |

---

## 8. AI 对话与会话管理

### 8.1 教师 AI 教研

| 方法   | 路径                                   | 说明             |
| ------ | -------------------------------------- | ---------------- |
| POST   | /api/teacher/chat                      | 教师 AI 对话     |
| POST   | /api/teacher/chat/stream               | 教师 AI 流式对话 |
| POST   | /api/teacher/chat/new-session          | 新建会话         |
| GET    | /api/teacher/chat/sessions             | 会话列表         |
| GET    | /api/teacher/chat/messages             | 会话消息         |
| DELETE | /api/teacher/chat/session/{session_id} | 删除会话         |

### 8.2 学生 AI 对话

| 方法   | 路径                                   | 说明         |
| ------ | -------------------------------------- | ------------ |
| POST   | /api/student/chat                      | 学生自由对话 |
| POST   | /api/student/chat/stream               | 学生流式对话 |
| POST   | /api/student/chat/new-session          | 新建会话     |
| GET    | /api/student/chat/sessions             | 会话列表     |
| GET    | /api/student/chat/messages             | 会话消息     |
| DELETE | /api/student/chat/session/{session_id} | 删除会话     |

### 8.3 学生情景对话

| 方法   | 路径                          | 说明             |
| ------ | ----------------------------- | ---------------- |
| GET    | /api/student/scene-chat/state | 获取情景会话状态 |
| DELETE | /api/student/scene-chat/clear | 清空情景会话     |
| POST   | /api/student/scene-chat       | 发送情景对话消息 |

---

## 9. 个人资料库（User KB）

| 方法   | 路径                          | 说明                   |
| ------ | ----------------------------- | ---------------------- |
| GET    | /api/user/kb/docs             | 私有资料列表           |
| POST   | /api/user/kb/upload           | 上传私有资料           |
| POST   | /api/user/kb/upload-temporary | 上传临时资料（会话级） |
| POST   | /api/user/kb/reindex/{doc_id} | 重新索引资料           |
| DELETE | /api/user/kb/docs/{doc_id}    | 删除资料               |

## 10. 常见状态码

| 状态码 | 含义             |
| ------ | ---------------- |
| 200    | 请求成功         |
| 401    | 未登录或鉴权失败 |
| 403    | 权限不足         |
| 404    | 资源不存在       |
| 500    | 服务器内部错误   |
