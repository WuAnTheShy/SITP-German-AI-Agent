import React, { useState, useEffect } from 'react';
import StudentLayout from '../../components/StudentLayout';
import request from '../../api/request';
import { API_FAVORITES_LIST, API_FAVORITES_DELETE, API_FAVORITES_AI_EXTEND, API_FAVORITES_ADD } from '../../api/config';

const FavoritesPage = () => {
  const [favList, setFavList] = useState([]);
  const [listLoading, setListLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [addLoading, setAddLoading] = useState(false);
  const [newFav, setNewFav] = useState({
    content: '',
    translate: '',
    rule: '',
    note: ''
  });

  useEffect(() => {
    const getFavList = async () => {
      setListLoading(true);
      try {
        const res = await request.get(API_FAVORITES_LIST);
        if (res.data.code === 200) setFavList(res.data.data);
        else alert(res.data.message || '获取收藏列表失败');
      } catch (err) { console.error('获取收藏列表接口报错：', err); alert('网络错误，获取收藏列表失败'); }
      finally { setListLoading(false); }
    };
    getFavList();
  }, []);

  const handleAddFav = async (e) => {
    e.preventDefault();
    if (!newFav.content.trim()) {
      alert('请输入收藏内容');
      return;
    }
    setAddLoading(true);
    try {
      const res = await request.post(API_FAVORITES_ADD, newFav);
      if (res.data.code === 200) {
        setFavList(prev => [res.data.data, ...prev]);
        setShowAddModal(false);
        setNewFav({
          content: '',
          translate: '',
          rule: '',
          note: ''
        });
      } else alert(res.data.message || '添加收藏失败');
    } catch (err) { alert('网络错误，添加收藏失败'); }
    finally { setAddLoading(false); }
  };

  const handleDeleteFav = async (id) => {
    if (!window.confirm('确定要删除这条收藏吗？')) return;
    setDeleteLoading(true);
    try {
      const res = await request.delete(`${API_FAVORITES_DELETE}/${id}`);
      if (res.data.code === 200) { setFavList(prev => prev.filter(item => item.id !== id)); }
      else alert(res.data.message || '删除失败');
    } catch (err) { alert('网络错误，删除失败'); }
    finally { setDeleteLoading(false); }
  };

  const handleAIExtend = async (item) => {
    setAiLoading(true);
    try {
      const res = await request.post(API_FAVORITES_AI_EXTEND, { content: item.content }, { timeout: 60000 });
      if (res.data.code === 200) alert(`🤖 AI拓展学习：\n${res.data.data.extendContent}`);
      else alert(res.data.message || 'AI拓展生成失败');
    } catch (err) { alert('网络错误，AI拓展生成失败'); }
    finally { setAiLoading(false); }
  };

  return (
    <StudentLayout>
      <div className="flex-1 overflow-y-auto p-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-200 mb-2">⭐ 我的学习收藏夹</h1>
            <p className="text-gray-500 dark:text-gray-400">收藏重点知识点，AI一键拓展，高效复习</p>
          </div>
          <button 
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            ✚ 新建收藏
          </button>
        </div>

        {/* 收藏列表 */}
        {listLoading ? (
          <p className="text-center text-gray-400 dark:text-gray-500 py-8">收藏内容加载中...</p>
        ) : favList.length === 0 ? (
          <div className="text-center py-16 text-gray-400 dark:text-gray-500">暂无收藏内容，点击右上角按钮新建收藏！🌟</div>
        ) : (
          <div className="space-y-4">
            {favList.map(item => (
              <div key={item.id} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
                <div className="mb-3">
                  <p className="font-medium text-gray-800 dark:text-gray-200 text-lg">{item.content}</p>
                  {item.translate && <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">💡 释义：{item.translate}</p>}
                  {item.rule && <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">📚 规则：{item.rule}</p>}
                  {item.note && <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">📝 备注：{item.note}</p>}
                </div>
                <div className="flex gap-3">
                  <button onClick={() => handleAIExtend(item)} disabled={aiLoading}
                    className="px-4 py-2 bg-blue-100 text-blue-700 dark:text-blue-400 rounded-lg hover:bg-blue-200 disabled:opacity-50 transition-colors text-sm font-medium">
                    {aiLoading ? '生成中...' : '🤖 AI拓展'}
                  </button>
                  <button onClick={() => handleDeleteFav(item.id)} disabled={deleteLoading}
                    className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 disabled:opacity-50 transition-colors text-sm">
                    {deleteLoading ? '删除中...' : '删除'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 新建收藏弹窗 */}
        {showAddModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">新建收藏</h3>
              <form onSubmit={handleAddFav}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">收藏内容 *</label>
                  <input 
                    type="text" 
                    value={newFav.content} 
                    onChange={(e) => setNewFav({...newFav, content: e.target.value})}
                    className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-gray-100 text-sm"
                    placeholder="例如：德语语法规则、词汇等"
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">释义（可选）</label>
                  <input 
                    type="text" 
                    value={newFav.translate} 
                    onChange={(e) => setNewFav({...newFav, translate: e.target.value})}
                    className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-gray-100 text-sm"
                    placeholder="例如：中文翻译、解释等"
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">规则（可选）</label>
                  <input 
                    type="text" 
                    value={newFav.rule} 
                    onChange={(e) => setNewFav({...newFav, rule: e.target.value})}
                    className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-gray-100 text-sm"
                    placeholder="例如：语法规则、使用方法等"
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">备注（可选）</label>
                  <textarea 
                    value={newFav.note} 
                    onChange={(e) => setNewFav({...newFav, note: e.target.value})}
                    className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-gray-100 text-sm"
                    placeholder="例如：个人笔记、重点标记等"
                    rows={3}
                  />
                </div>
                <div className="flex gap-2">
                  <button type="button" onClick={() => setShowAddModal(false)} className="flex-1 py-2 rounded-lg border border-gray-200 dark:border-white/10 text-gray-700 dark:text-gray-300 text-sm font-medium">取消</button>
                  <button type="submit" disabled={addLoading} className="flex-1 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium disabled:opacity-50">{addLoading ? '添加中...' : '确认添加'}</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </StudentLayout>
  );
};

export default FavoritesPage;
