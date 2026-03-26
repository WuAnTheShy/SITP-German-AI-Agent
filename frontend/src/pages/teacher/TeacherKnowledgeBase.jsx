import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { parseStoredUserInfo } from '../../utils/safeJson';
import request from '../../api/request';
import { API_USER_KB_DELETE, API_USER_KB_DOCS, API_USER_KB_REINDEX, API_USER_KB_UPLOAD } from '../../api/config';

const STATUS_LABEL = {
    ready: '可用',
    processing: '处理中',
    failed: '失败',
};

const STATUS_CLASS = {
    ready: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
    processing: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
    failed: 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300',
};

const TeacherKnowledgeBase = () => {
    const navigate = useNavigate();
    const [docs, setDocs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [uploading, setUploading] = useState(false);
    const [reindexingId, setReindexingId] = useState(null);
    const [deletingId, setDeletingId] = useState(null);
    const [query, setQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');

    const userInfo = parseStoredUserInfo();

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
        if (!file || uploading) return;
        const fd = new FormData();
        fd.append('file', file);
        try {
            setUploading(true);
            await request.post(API_USER_KB_UPLOAD, fd, {
                headers: { 'Content-Type': 'multipart/form-data' },
                timeout: 600000,
            });
            await fetchDocs();
        } catch (err) {
            alert(err.response?.data?.detail || err.message || '上传失败');
        } finally {
            setUploading(false);
            e.target.value = '';
        }
    };

    const reindex = async (id) => {
        try {
            setReindexingId(id);
            await request.post(`${API_USER_KB_REINDEX}/${id}`, {}, { timeout: 600000 });
            await fetchDocs();
        } catch (err) {
            alert(err.response?.data?.detail || err.message || '重建失败');
        } finally {
            setReindexingId(null);
        }
    };

    const remove = async (id) => {
        if (!window.confirm('确认删除该文档？')) return;
        try {
            setDeletingId(id);
            await request.delete(`${API_USER_KB_DELETE}/${id}`);
            await fetchDocs();
        } catch (err) {
            alert(err.response?.data?.detail || err.message || '删除失败');
        } finally {
            setDeletingId(null);
        }
    };

    const longTermDocs = docs.filter((d) => !d.is_temporary);
    const filteredDocs = longTermDocs.filter((d) => {
        const hitStatus = statusFilter === 'all' ? true : d.status === statusFilter;
        const q = query.trim().toLowerCase();
        const hitQuery = !q
            ? true
            : String(d.title || '').toLowerCase().includes(q) || String(d.source_name || '').toLowerCase().includes(q);
        return hitStatus && hitQuery;
    });

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4 md:p-8">
            <div className="max-w-5xl mx-auto space-y-6">
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-200">我的资料库（长期资料）</h1>
                        <p className="text-gray-500 dark:text-gray-400 mt-1">这里上传的是长期资料，会在你的所有会话中可用；对话页仅上传当前会话临时资料。</p>
                    </div>
                    <div className="flex gap-2">
                        <button onClick={() => navigate(`/teacher/${userInfo.id}/dashboard`)} className="px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 text-sm text-gray-700 dark:text-gray-300">返回控制台</button>
                        <label className={`px-4 py-2 rounded-lg transition-colors text-sm font-medium ${uploading ? 'bg-blue-400 cursor-wait text-white' : 'bg-blue-600 hover:bg-blue-700 text-white cursor-pointer'}`}>
                            {uploading ? '上传中…' : '上传长期资料'}
                            <input type="file" accept=".pdf,.txt,.md" className="hidden" onChange={onUpload} />
                        </label>
                    </div>
                </div>
                <div className="mb-4 flex flex-wrap gap-2 items-center">
                    <input
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="按标题/文件名搜索"
                        className="px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-700 dark:text-gray-200 min-w-[220px]"
                    />
                    <div className="flex gap-1">
                        {['all', 'ready', 'processing', 'failed'].map((s) => (
                            <button
                                key={s}
                                type="button"
                                onClick={() => setStatusFilter(s)}
                                className={`px-2.5 py-1.5 text-xs rounded-md border ${statusFilter === s ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300'}`}
                            >
                                {s === 'all' ? '全部状态' : STATUS_LABEL[s]}
                            </button>
                        ))}
                    </div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">共 {longTermDocs.length} 份，当前显示 {filteredDocs.length} 份</span>
                </div>
                {error && <div className="text-sm text-red-500">{error}</div>}
                {loading ? (
                    <div className="text-gray-400">加载中...</div>
                ) : longTermDocs.length === 0 ? (
                    <div className="text-gray-500">暂无长期资料。</div>
                ) : filteredDocs.length === 0 ? (
                    <div className="text-gray-500">没有匹配当前筛选条件的资料。</div>
                ) : (
                    <div className="space-y-3">
                        {filteredDocs.map((d) => (
                            <div key={d.id} className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                                <div className="flex items-center gap-2 flex-wrap">
                                    <div className="font-medium text-gray-800 dark:text-gray-200">{d.title}</div>
                                    <span className={`inline-flex px-2 py-0.5 rounded text-xs ${STATUS_CLASS[d.status] || 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200'}`}>
                                        {STATUS_LABEL[d.status] || d.status}
                                    </span>
                                </div>
                                <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                    {d.source_name} · 类型: 长期 · 切片: {d.chunk_count ?? 0}
                                </div>
                                {d.error_message && <div className="text-xs text-red-500 mt-1">{d.error_message}</div>}
                                <div className="mt-3 flex gap-2">
                                    <button
                                        onClick={() => reindex(d.id)}
                                        disabled={reindexingId === d.id}
                                        className="px-3 py-1.5 rounded-md bg-blue-50 text-blue-600 text-sm disabled:opacity-60"
                                    >
                                        {reindexingId === d.id ? '重建中…' : '重建索引'}
                                    </button>
                                    <button
                                        onClick={() => remove(d.id)}
                                        disabled={deletingId === d.id}
                                        className="px-3 py-1.5 rounded-md bg-red-50 text-red-600 text-sm disabled:opacity-60"
                                    >
                                        {deletingId === d.id ? '删除中…' : '删除'}
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default TeacherKnowledgeBase;
