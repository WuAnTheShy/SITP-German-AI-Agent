import React, { useEffect, useState } from 'react';
import StudentLayout from '../../components/StudentLayout';
import request from '../../api/request';
import { API_USER_KB_DELETE, API_USER_KB_DOCS, API_USER_KB_REINDEX, API_USER_KB_UPLOAD } from '../../api/config';

const MyKnowledgeBase = () => {
    const [docs, setDocs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const fetchDocs = async () => {
        setLoading(true);
        setError('');
        try {
            const res = await request.get(API_USER_KB_DOCS, { timeout: 60000 });
            setDocs(Array.isArray(res.data) ? res.data : []);
        } catch (e) {
            setError(e.response?.data?.detail || e.message || '加载失败');
            setDocs([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDocs();
    }, []);

    const onUpload = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const fd = new FormData();
        fd.append('file', file);
        try {
            await request.post(API_USER_KB_UPLOAD, fd, {
                headers: { 'Content-Type': 'multipart/form-data' },
                timeout: 600000,
            });
            await fetchDocs();
        } catch (err) {
            alert(err.response?.data?.detail || err.message || '上传失败');
        } finally {
            e.target.value = '';
        }
    };

    const reindex = async (id) => {
        try {
            await request.post(`${API_USER_KB_REINDEX}/${id}`, {}, { timeout: 600000 });
            await fetchDocs();
        } catch (err) {
            alert(err.response?.data?.detail || err.message || '重建失败');
        }
    };

    const remove = async (id) => {
        if (!window.confirm('确认删除该文档？')) return;
        try {
            await request.delete(`${API_USER_KB_DELETE}/${id}`);
            await fetchDocs();
        } catch (err) {
            alert(err.response?.data?.detail || err.message || '删除失败');
        }
    };

    return (
        <StudentLayout>
            <div className="flex-1 overflow-y-auto p-8">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-200 mb-2">我的资料库（长期资料）</h1>
                        <p className="text-gray-500 dark:text-gray-400">这里上传的是长期资料，会在你的所有会话中可用；对话页仅上传当前会话临时资料。</p>
                    </div>
                    <label className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium cursor-pointer">
                        上传长期资料
                        <input type="file" accept=".pdf,.txt,.md" className="hidden" onChange={onUpload} />
                    </label>
                </div>
                {error && <div className="mb-4 text-sm text-red-500">{error}</div>}
                {loading ? (
                    <p className="text-gray-400">加载中...</p>
                ) : docs.filter((d) => !d.is_temporary).length === 0 ? (
                    <div className="text-gray-500">暂无长期资料，上传后即可在所有会话中使用。</div>
                ) : (
                    <div className="space-y-3">
                        {docs.filter((d) => !d.is_temporary).map((d) => (
                            <div key={d.id} className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                                <div className="font-medium text-gray-800 dark:text-gray-200">{d.title}</div>
                                <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                    {d.source_name} · 类型: 长期 · 状态: {d.status} · 切片: {d.chunk_count ?? 0}
                                </div>
                                {d.error_message && <div className="text-xs text-red-500 mt-1">{d.error_message}</div>}
                                <div className="mt-3 flex gap-2">
                                    <button onClick={() => reindex(d.id)} className="px-3 py-1.5 rounded-md bg-blue-50 text-blue-600 text-sm">重建索引</button>
                                    <button onClick={() => remove(d.id)} className="px-3 py-1.5 rounded-md bg-red-50 text-red-600 text-sm">删除</button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </StudentLayout>
    );
};

export default MyKnowledgeBase;
