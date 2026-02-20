import React, { useState } from 'react';
import axios from 'axios';

const FavoritesPage = () => {
  const [favCates, setFavCates] = useState([]);
  const [selectedType, setSelectedType] = useState('');
  const [favList, setFavList] = useState([]);
  const [cateLoading, setCateLoading] = useState(false);
  const [listLoading, setListLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);

  React.useEffect(() => {
    const getCateList = async () => {
      setCateLoading(true);
      try {
        const res = await axios.get('/api/student/favorites/categories');
        if (res.data.code === 200) {
          const cateList = res.data.data;
          setFavCates(cateList);
          if (cateList.length > 0) {
            setSelectedType(cateList[0].type);
          }
        } else {
          alert(res.data.message || '获取收藏分类失败');
        }
      } catch (err) {
        console.error('获取收藏分类接口报错：', err);
        alert('网络错误，获取收藏分类失败，请稍后重试');
      } finally {
        setCateLoading(false);
      }
    };
    getCateList();
  }, []);

  React.useEffect(() => {
    if (!selectedType) return;
    const getFavList = async () => {
      setListLoading(true);
      try {
        const res = await axios.get('/api/student/favorites/list', {
          params: { type: selectedType }
        });
        if (res.data.code === 200) {
          setFavList(res.data.data);
        } else {
          alert(res.data.message || '获取收藏列表失败');
        }
      } catch (err) {
        console.error('获取收藏列表接口报错：', err);
        alert('网络错误，获取收藏列表失败，请稍后重试');
      } finally {
        setListLoading(false);
      }
    };
    getFavList();
  }, [selectedType]);

  const handleChangeType = (type) => {
    setSelectedType(type);
  };

  const handleDeleteFav = async (id) => {
    if (!window.confirm('确定要删除这条收藏吗？删除后无法恢复')) return;
    setDeleteLoading(true);
    try {
      const res = await axios.delete(`/api/student/favorites/${id}`);
      if (res.data.code === 200) {
        setFavList(prev => prev.filter(item => item.id !== id));
        alert('已从收藏夹中移除！');
      } else {
        alert(res.data.message || '删除失败');
      }
    } catch (err) {
      console.error('删除收藏接口报错：', err);
      alert('网络错误，删除失败，请稍后重试');
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleAIExtend = async (item) => {
    setAiLoading(true);
    try {
      const res = await axios.post('/api/student/favorites/ai-extend', {
        content: item.content,
        type: selectedType
      });
      if (res.data.code === 200) {
        alert(`🤖 AI拓展学习：\n${res.data.data.extendContent}`);
      } else {
        alert(res.data.message || 'AI拓展生成失败');
      }
    } catch (err) {
      console.error('AI拓展接口报错：', err);
      alert('网络错误，AI拓展生成失败，请稍后重试');
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <div className="favorites-page">
      <div className="page-header">
        <h1>我的学习收藏夹</h1>
        <p>收藏重点知识点，AI一键拓展，高效复习</p>
      </div>

      <div className="fav-cate-switch">
        {cateLoading ? (
          <div className="loading-tip">分类加载中...</div>
        ) : (
          favCates.map(cate => (
            <button
              key={cate.id}
              className={selectedType === cate.type ? 'active' : ''}
              onClick={() => handleChangeType(cate.type)}
              disabled={listLoading}
            >
              {cate.name}
            </button>
          ))
        )}
      </div>

      <div className="fav-list-section">
        {listLoading ? (
          <div className="loading-tip">收藏内容加载中...</div>
        ) : favList.length === 0 ? (
          <div className="no-fav-tip">该分类暂无收藏内容，快去学习收藏吧！🌟</div>
        ) : (
          <div className="fav-list">
            {favList.map(item => (
              <div key={item.id} className="fav-item">
                <div className="fav-content">
                  <p className="main">{item.content}</p>
                  {item.translate && <p className="trans">💡 释义：{item.translate}</p>}
                  {item.rule && <p className="rule">📚 规则：{item.rule}</p>}
                  {item.note && <p className="note">📝 备注：{item.note}</p>}
                </div>
                <div className="fav-btns">
                  <button
                    onClick={() => handleAIExtend(item)}
                    className="extend-btn"
                    disabled={aiLoading}
                  >
                    {aiLoading ? '生成中...' : '🤖 AI拓展'}
                  </button>
                  <button
                    onClick={() => handleDeleteFav(item.id)}
                    className="delete-btn"
                    disabled={deleteLoading}
                  >
                    {deleteLoading ? '删除中...' : '删除'}
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

export default FavoritesPage;