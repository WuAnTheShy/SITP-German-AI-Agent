import React, { useState } from 'react';

const FavoritesPage = () => {
  // 收藏分类（覆盖德语学习核心收藏类型）
  const [favCates, setFavCates] = useState([
    { id: 1, name: "收藏词汇", type: "vocab" },
    { id: 2, name: "收藏例句", type: "sentence" },
    { id: 3, name: "收藏语法", type: "grammar" },
    { id: 4, name: "收藏对话", type: "dialog" },
  ]);
  // 当前选中分类、模拟收藏数据
  const [selectedType, setSelectedType] = useState('vocab');
  const [favList, setFavList] = useState({
    vocab: [
      { id: 101, content: "Schönheit", translate: "美丽，美貌", note: "阴性名词，die Schönheit" },
      { id: 102, content: "Selbstvertrauen", translate: "自信", note: "中性名词，das Selbstvertrauen" },
      { id: 103, content: "bestreben", translate: "努力，力求", note: "动词，sich nach etw. streben" }
    ],
    sentence: [
      { id: 201, content: "Das Leben ist wie ein Fahrrad, man muss sich bewegen, um nicht umzufallen.", translate: "生活就像自行车，必须前进才能不倒下。", note: "爱因斯坦名言" },
      { id: 202, content: "Jeder Tag bringt neue Möglichkeiten.", translate: "每一天都带来新的可能。", note: "日常高频句" }
    ],
    grammar: [
      { id: 301, content: "带zu的不定式", rule: "部分动词后接带zu的不定式，如wollen, hoffen, versuchen...", note: "z.B. Ich hoffe, ins Ausland zu studieren." },
      { id: 302, content: "第二格所有格", rule: "表示所属关系，阳性/中性名词第二格加-s，阴性/复数不变", note: "z.B. das Buch meines Vaters" }
    ],
    dialog: [
      { id: 401, content: "— Wie geht es dir? — Danke, gut! Und dir? — Auch gut.", translate: "— 你好吗？— 谢谢，很好！你呢？— 我也很好。", note: "日常问候基础对话" },
      { id: 402, content: "— Wohin gehst du? — Ich gehe zur Bibliothek. — Viel Spaß! — Danke.", translate: "— 你要去哪？— 我去图书馆。— 玩得开心！— 谢谢。", note: "出行询问对话" }
    ]
  });

  // 切换收藏分类
  const handleChangeType = (type) => {
    setSelectedType(type);
  };

  // 删除收藏项
  const handleDeleteFav = (id) => {
    setFavList(prev => ({
      ...prev,
      [selectedType]: prev[selectedType].filter(item => item.id !== id)
    }));
    alert("已从收藏夹中移除！");
  };

  // AI拓展学习
  const handleAIExtend = (item) => {
    alert(`🤖 AI拓展学习：已为你生成【${item.content}】的相关拓展内容（同类词汇/例句/语法应用），快去查看吧！`);
  };

  return (
    <div className="favorites-page">
      <div className="page-header">
        <h1>我的学习收藏夹</h1>
        <p>收藏重点知识点，AI一键拓展，高效复习</p >
      </div>

      {/* 收藏分类切换 */}
      <div className="fav-cate-switch">
        {favCates.map(cate => (
          <button
            key={cate.id}
            className={selectedType === cate.type ? 'active' : ''}
            onClick={() => handleChangeType(cate.type)}
          >
            {cate.name}
          </button>
        ))}
      </div>

      {/* 收藏列表展示 */}
      <div className="fav-list-section">
        {favList[selectedType].length === 0 ? (
          <div className="no-fav-tip">该分类暂无收藏内容，快去学习收藏吧！🌟</div>
        ) : (
          <div className="fav-list">
            {favList[selectedType].map(item => (
              <div key={item.id} className="fav-item">
                <div className="fav-content">
                  <p className="main">{item.content}</p >
                  {item.translate && <p className="trans">💡 释义：{item.translate}</p >}
                  {item.rule && <p className="rule">📚 规则：{item.rule}</p >}
                  {item.note && <p className="note">📝 备注：{item.note}</p >}
                </div>
                <div className="fav-btns">
                  <button onClick={() => handleAIExtend(item)} className="extend-btn">🤖 AI拓展</button>
                  <button onClick={() => handleDeleteFav(item.id)} className="delete-btn">删除</button>
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
