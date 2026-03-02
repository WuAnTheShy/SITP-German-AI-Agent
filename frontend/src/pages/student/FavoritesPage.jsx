import React, { useState, useEffect } from 'react';
import StudentLayout from '../../components/StudentLayout';
import axios from 'axios';

const FavoritesPage = () => {
  const [favCates, setFavCates] = useState([]);
  const [selectedType, setSelectedType] = useState('');
  const [favList, setFavList] = useState([]);
  const [cateLoading, setCateLoading] = useState(false);
  const [listLoading, setListLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);

  useEffect(() => {
    const getCateList = async () => {
      setCateLoading(true);
      try {
        const res = await axios.get('/api/student/favorites/categories');
        if (res.data.code === 200) {
          const cateList = res.data.data;
          setFavCates(cateList);
          if (cateList.length > 0) setSelectedType(cateList[0].type);
        } else alert(res.data.message || '获取收藏分类失败');
      } catch (err) { console.error('获取收藏分类接口报错：', err); alert('网络错误，获取收藏分类失败'); }
      finally { setCateLoading(false); }
    };
    getCateList();
  }, []);

  useEffect(() => {
    if (!selectedType) return;
    const getFavList = async () => {
      setListLoading(true);
      try {
        const res = await axios.get('/api/student/favorites/list', { params: { type: selectedType } });
        if (res.data.code === 200) setFavList(res.data.data);
        else alert(res.data.message || '获取收藏列表失败');
      } catch (err) { console.error('获取收藏列表接口报错：', err); alert('网络错误，获取收藏列表失败'); }
      finally { setListLoading(false); }
    };
    getFavList();
  }, [selectedType]);

  const handleDeleteFav = async (id) => {
    if (!window.confirm('确定要删除这条收藏吗？')) return;
    setDeleteLoading(true);
    try {
      const res = await axios.delete(`/api/student/favorites/${id}`);
      if (res.data.code === 200) { setFavList(prev => prev.filter(item => item.id !== id)); }
      else alert(res.data.message || '删除失败');
    } catch (err) { alert('网络错误，删除失败'); }
    finally { setDeleteLoading(false); }
  };

  const handleAIExtend = async (item) => {
    setAiLoading(true);
    try {
      const res = await axios.post('/api/student/favorites/ai-extend', { content: item.content, type: selectedType });
      if (res.data.code === 200) alert(`🤖 AI拓展学习：\n${res.data.data.extendContent}`);
      else alert(res.data.message || 'AI拓展生成失败');
    } catch (err) { alert('网络错误，AI拓展生成失败'); }
    finally { setAiLoading(false); }
  };

  return (
    <StudentLayout>
      <div className="flex-1 overflow-y-auto p-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-800 mb-2">⭐ 我的学习收藏夹</h1>
          <p className="text-gray-500">收藏重点知识点，AI一键拓展，高效复习</p>
        </div>

        {/* 分类切换 */}
        <div className="flex gap-3 flex-wrap mb-6">
          {cateLoading ? (
            <p className="text-gray-400">分类加载中...</p>
          ) : favCates.map(cate => (
            <button key={cate.id} onClick={() => setSelectedType(cate.type)} disabled={listLoading}
              className={`px-4 py-3 rounded-lg border-2 transition-all ${
                selectedType === cate.type ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 bg-white hover:border-blue-300 text-gray-700'
              }`}>
              {cate.name}
            </button>
          ))}
        </div>

        {/* 收藏列表 */}
        {listLoading ? (
          <p className="text-center text-gray-400 py-8">收藏内容加载中...</p>
        ) : favList.length === 0 ? (
          <div className="text-center py-16 text-gray-400">该分类暂无收藏内容，快去学习收藏吧！🌟</div>
        ) : (
          <div className="space-y-4">
            {favList.map(item => (
              <div key={item.id} className="bg-white rounded-xl border border-gray-200 p-5">
                <div className="mb-3">
                  <p className="font-medium text-gray-800 text-lg">{item.content}</p>
                  {item.translate && <p className="text-sm text-gray-600 mt-1">💡 释义：{item.translate}</p>}
                  {item.rule && <p className="text-sm text-gray-600 mt-1">📚 规则：{item.rule}</p>}
                  {item.note && <p className="text-sm text-gray-500 mt-1">📝 备注：{item.note}</p>}
                </div>
                <div className="flex gap-3">
                  <button onClick={() => handleAIExtend(item)} disabled={aiLoading}
                    className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 disabled:opacity-50 transition-colors text-sm font-medium">
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
      </div>
    </StudentLayout>
  );
};

export default FavoritesPage;
