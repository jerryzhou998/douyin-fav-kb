TEMPLATE = html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>我的抖音收藏 · 三层脑图</title>
<style>
:root{--bg:#f7f7fb;--card:#fff;--line:#e3e3ee;--text:#2b2b35;--muted:#8a8a99;--accent2:#3b6cff;}
.item .desc{font-size:12px;color:#666;line-height:1.55;margin-top:2px}
.fulltext{font-size:11px;color:#8a8a99;line-height:1.4;display:block;margin-top:2px}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;background:var(--bg);color:var(--text);height:100vh;display:flex;flex-direction:column}
header{padding:12px 22px;background:#fff;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:14px;flex-wrap:wrap}
header h1{font-size:18px;margin:0;font-weight:700}
.search-wrap{flex:1;min-width:220px;display:flex;gap:8px}
#q{flex:1;padding:9px 12px;border:1px solid #d5d5e0;border-radius:10px;font-size:14px;outline:none}
.badge{background:#f2f2f8;color:var(--muted);border-radius:20px;padding:4px 12px;font-size:13px;white-space:nowrap}
main{flex:1;display:flex;overflow:hidden}
.left{width:340px;min-width:340px;border-right:1px solid var(--line);overflow:auto;background:#fff;padding:12px}
.right{flex:1;overflow:auto;padding:18px 24px}
.cat{font-size:13px;font-weight:700;color:#fff;background:var(--accent2);border-radius:8px;padding:6px 10px;margin:12px 0 2px;cursor:pointer}
.sub{font-size:12px;font-weight:600;color:#444;padding:5px 8px 2px 10px}
.item{display:flex;flex-direction:column;gap:2px;padding:7px 10px;border-radius:8px;margin:2px 0;cursor:pointer;border:1px solid transparent}
.item:hover{background:#f2f4ff;border-color:#cdd5ff}
.item .t{font-size:13.5px;font-weight:600;line-height:1.35}
.item .m{font-size:11.5px;color:var(--muted)}
.item .u{font-size:11.5px;color:var(--accent2)}
.rtree{padding-left:0;list-style:none}
.rtree ul{margin:3px 0 3px 16px;padding-left:14px;border-left:2px solid var(--line)}
.rtree li{margin:2px 0}
.node{display:flex;align-items:center;gap:8px;padding:3px 6px;border-radius:6px;cursor:pointer;font-size:13px}
.node:hover{background:#eef1ff}
.node .chip{min-width:22px;height:18px;line-height:18px;border-radius:5px;color:#fff;font-size:10px;text-align:center;padding:0 4px}
.node.l1{font-weight:700;font-size:14px}
.node.l2{font-weight:600;color:#3c3c4a}
.node.l3{font-weight:500;color:#5a5a6b}
.leaf{display:inline-block;color:#444;text-decoration:none;cursor:pointer;margin:1px 0;font-size:12.5px;line-height:1.4;border-left:2px solid #cdd5ff;padding-left:8px}
.leaf .tt{color:var(--accent2)}
.leaf:hover{text-decoration:underline}
.empty{color:var(--muted);padding:30px;text-align:center}
.mark{background:#ffe29a;border-radius:3px;padding:0 2px}
.page-note{font-size:12px;color:var(--muted);margin-top:14px;line-height:1.7}
@media(max-width:760px){main{flex-direction:column}.left{width:100%;min-width:0;max-height:38vh;border-right:none;border-bottom:1px solid var(--line)}}
</style>
</head>
<body>
<header>
  <h1>🧠 我的抖音收藏 · 三层脑图</h1>
  <div class="search-wrap"><input id="q" placeholder="搜索标题 / 话题 / 全文，回车定位" autocomplete="off"></div>
  <span class="badge" id="total"></span>
</header>
<main>
  <div class="left" id="list"></div>
  <div class="right"><h2>🌳 脑图</h2><div class="rtree" id="tree"></div>
    <div class="page-note">一级分类按专题分组，二级/三级逐级展开；点击任意视频标题在新标签页打开并播放。搜索支持标题、话题、全文关键词，命中后左栏即时筛选。</div>
  </div>
</main>
<script>
const DATA = __DATA__;
const TOTAL = DATA.reduce((a,c)=>a+c.count,0);
let expanded = {};
const PALL1 = {'智能机器人':'#e11d48','AI 与智能':'#ff2656','编程与开源':'#3b6cff','教育与成长':'#12b76a','副业与赚钱':'#f59e0b','生活与健康':'#10b981','美食与三农':'#ea5b3c','旅行与摄影':'#0891b2','金融与财经':'#8b5cf6','影视娱乐与情感':'#ec4899','设计与办公':'#6366f1','其他':'#64748b'};
function col(c){ return PALL1[c]||'#64748b'; }
function esc(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function mark(s,q){ if(!q) return esc(s); const t=String(s),i=t.toLowerCase().indexOf(q.toLowerCase()); if(i<0) return esc(t); return esc(t.slice(0,i))+'<span class="mark">'+esc(t.slice(i,i+q.length))+'</span>'+esc(t.slice(i+q.length)); }
function allItems(n, acc, path){ acc=acc||[]; const p=(path? path+[''].join(' › '):'') ; const pp = path? (path+' › '+n.name) : n.name; n.items.forEach(it=>acc.push({it,p:pp})); (n.children||[]).forEach(c=>allItems(c, acc, pp)); return acc; }
function flatSearch(nodes,q){ const arr=[]; nodes.forEach(n=>allItems(n,arr,'')); const ql=(q||'').trim().toLowerCase(); if(!ql) return {items:arr}; return {items:arr.filter(o=> (o.it.t+' '+(o.it.text||'')+' '+(o.it.tags||'')).toLowerCase().indexOf(ql)>=0)}; }
function cleanNum(x){ return String(x||'').replace(/^\s*\d+\s*/, '').replace(/\s+/g,' ').trim(); }
function makeCard(o,q,cat){ const d=document.createElement('div'); d.className='item'; const t=document.createElement('span'); t.className='t'; t.innerHTML=mark(cleanNum(o.it.t),q); const m=document.createElement('span'); m.className='m'; m.textContent=(o.p? o.p+' · ':'')+(o.it.tags?'#'+o.it.tags.split(/[，, ]+/).filter(Boolean).slice(0,8).join(' #'):''); const desc=document.createElement('div'); desc.className='desc'; desc.textContent=cleanNum(o.it.full||'').slice(0,400); const u=document.createElement('span'); u.className='u'; u.textContent='▶ 播放 '+o.it.u; d.appendChild(t); d.appendChild(m); d.appendChild(desc); d.appendChild(u); d.onclick=()=>window.open(o.it.u,'_blank'); return d; }
function renderLeft(q){
  const el=document.getElementById('list'); el.innerHTML='';
  const ql=(q||'').trim().toLowerCase();
  const all=[];
  DATA.forEach(n=>allItems(n,all,''));
  const shown = ql? all.filter(o=>(o.it.t+' '+(o.it.text||'')+' '+(o.it.tags||'')).toLowerCase().includes(ql)) : all;
  document.getElementById('total').textContent = ql? ('命中 '+shown.length+' / '+TOTAL+' 条') : ('共 '+TOTAL+' 条');
  if(!ql){
    DATA.forEach(n=>{
      const h=document.createElement('div'); h.className='cat'; h.style.background=col(n.name);
      h.textContent=n.name+'（'+n.count+'条）'; h.onclick=()=>{expanded[n.name]=!expanded[n.name]; renderLeft(''); renderTree();}; el.appendChild(h);
      if(expanded[n.name]===undefined) expanded[n.name]=true;
      if(expanded[n.name]){ const subItems=allItems(n,[],''); subItems.forEach(o=>el.appendChild(makeCard(o,'',n.name))); }
    });
  } else {
    shown.forEach(o=>el.appendChild(makeCard(o,ql,col('其他'))));
  }
}
function renderTree(){
  const el=document.getElementById('tree'); el.innerHTML='';
  const ul=document.createElement('ul');
  function put(n, depth, li){
    const node=document.createElement('div'); node.className='node l'+depth;
    const chip=document.createElement('span'); chip.className='chip'; chip.style.background=depth===1?col(n.name):'#8b95a1';
    chip.textContent=n.count;
    const nm=document.createElement('span'); nm.textContent=n.name+'（'+n.count+'条）';
    node.appendChild(chip); node.appendChild(nm);
    const key=n.name;
    if(expanded[key]===undefined) expanded[key]=depth===1;
    node.onclick=()=>{expanded[key]=!expanded[key]; renderTree();};
    li.appendChild(node);
    const sub=document.createElement('ul'); sub.style.display=expanded[key]?'block':'none';
      n.items.forEach(it=>{ const li2=document.createElement('li'); const a=document.createElement('a'); a.className='leaf'; a.href=it.u; a.target='_blank'; a.rel='noopener'; const tn=document.createElement('span'); tn.className='tt'; tn.textContent='▶ '+cleanNum(it.t); a.appendChild(tn); const fm=document.createElement('span'); fm.className='fulltext'; fm.textContent=cleanNum(it.full||'').slice(0,300); a.appendChild(document.createElement('br')); a.appendChild(fm); a.title=cleanNum(it.full||it.t); li2.appendChild(a); sub.appendChild(li2); });
    n.children.forEach(c=>{ const li2=document.createElement('li'); put(c,depth+1,li2); sub.appendChild(li2); });
    li.appendChild(sub);
  }
  DATA.forEach(n=>{ const li=document.createElement('li'); put(n,1,li); ul.appendChild(li); });
  el.appendChild(ul);
}
document.getElementById('q').addEventListener('input',()=>renderLeft(document.getElementById('q').value));
document.getElementById('q').addEventListener('keydown',e=>{ if(e.key==='Enter') renderLeft(document.getElementById('q').value); });
renderLeft('');
renderTree();
</script>
</body>
</html>
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""收藏数据 → 三级分类树（同层并列、同维度）→ 可搜索脑图网页
"""
import argparse, json, re, csv
from pathlib import Path

# ============ 人工修正（少量抓取脏数据/规则难判的条目） ============
OVERRIDES = {
    "7627501463777856774": ["AI 与智能", "AI 编程与开发", "浏览器自动化"],
    "7545299764854705449": ["AI 与智能", "大模型与语言模型", "API 接入"],
    "7484467999416651048": ["AI 与智能", "AI 智能体", "微信数字助理"],
    "7675634780884454682": ["AI 与智能", "AI 智能体", "数字员工"],
    "7656761622077197611": ["其他", "其他", "其他"],
    "7264167225798561061": ["其他", "其他", "其他"],
    "7498307443101797695": ["编程与开源", "效率工具", "文件互传工具"],
    "7454634022732401939": ["旅行与摄影", "旅行", "阿联酋头等舱"],
    "7454634022732401935": ["旅行与摄影", "旅行", "阿联酋头等舱"],
    "7632311437809011977": ["旅行与摄影", "旅行", "北京周边游"],
    "7522280837623926056": ["旅行与摄影", "旅行", "城市旅游"],
    "7453863291660619047": ["教育与成长", "通识/文化", "历史人文"],
    "7479592514773667081": ["教育与成长", "通识/文化", "数学文化"],
    "7477122179906145555": ["教育与成长", "育儿/亲子", "专注力游戏"],
    "7505362573773802762": ["金融与财经", "宏观/政策", "美联储降息"],
    "7437412003603320123": ["教育与成长", "英语学习", "英语语法"],
    "7510948906625944891": ["设计与办公", "PPT/演示", "述职汇报"],
    "7478562120087375114": ["智能机器人", "四足/机器狗", "小米铁蛋"],
    "7476383791578238259": ["旅行与摄影", "旅行", "京津冀自驾"],
    "7667222893256351739": ["旅行与摄影", "修图/后期", "调色技巧"],
    "7615536162274381090": ["副业与赚钱", "自媒体", "短视频运营"],
    "7572471980651000806": ["副业与赚钱", "自媒体", "剪辑运营"],
    "7643287235898395919": ["编程与开源", "开发/框架", "机器学习"],
    "7664353974690090249": ["AI 与智能", "大模型与语言模型", "Kimi 玩法"],
    "7617837428543445184": ["AI 与智能", "AI 智能体", "开源 Agent"],
    "7537258097704045843": ["生活与健康", "健康/医疗", "中医"],
}

def is_hardware_robot(t):
    """只有真·硬件机器人关键词才算机器人（排除软件自动化）。"""
    strong = ["宇树", "unitree", "机器狗", "四足", "人形机器人", "仿生机器人",
              "灵巧手", "机械臂", "机器人保姆", "机器鸭", "microduck", "pollenrobotics",
              "工业机器狗", "建筑机器人", "拧螺丝机器人", "两栖机器人", "高仿真机器人",
              "具身", "实体智能", "实体机器人", "触觉", "机器人手套", "铁蛋"]
    return any(k in t for k in strong)

# ============ 分类规则 ============
# 结构：(一级, 二级, 三级, [关键词])；同一父级下，二级是同一维度、三级是同一维度（多为品牌/具体/其他）
RULES = [
    # ---------- 智能机器人：二级=形态/类型 ─────
    ("智能机器人", "人形机器人", "宇树", ["宇树", "unitree"]),
    ("智能机器人", "人形机器人", "傅利叶", ["傅利叶", "furui"]),
    ("智能机器人", "人形机器人", "其他", ["人形机器人", "人形"]),
    ("智能机器人", "四足/机器狗", "小米铁蛋", ["铁蛋", "小米机器狗"]),
    ("智能机器人", "四足/机器狗", "其他", ["机器狗", "四足", "工业机器狗"]),
    ("智能机器人", "机械臂/灵巧手", "其他", ["灵巧手", "机械臂", "夹爪"]),
    ("智能机器人", "桌面/小型机器人", "其他", ["桌面机器人", "机器鸭", "microduck", "pollenrobotics", "教育机器人"]),
    ("智能机器人", "仿生/两栖", "其他", ["仿生机器人", "两栖机器人"]),
    ("智能机器人", "特种/作业机器人", "建筑/施工", ["建筑机器人", "拧螺丝机器人", "木工机器人", "铺地板机器人"]),
    ("智能机器人", "特种/作业机器人", "消防/应急", ["消防机器人", "巡检机器人", "救灾机器人"]),
    ("智能机器人", "具身智能/感知", "机器人保姆", ["机器人保姆"]),
    ("智能机器人", "具身智能/感知", "具身数据集", ["具身", "触觉"]),
    ("智能机器人", "其他", "其他", ["机器人", "实体机器人", "实体智能"]),

    # ---------- AI 与智能：二级=功能方向 ─────
    ("AI 与智能", "大模型与语言模型", "DeepSeek", ["deepseek"]),
    ("AI 与智能", "大模型与语言模型", "GPT/Claude/Gemini", ["gpt", "claude", "gemini", "chatgpt"]),
    ("AI 与智能", "大模型与语言模型", "Kimi 等", ["kimi", "豆包", "智谱", "通义", "文心一言", "qwen"]),
    ("AI 与智能", "大模型与语言模型", "其他", ["llm", "大模型", "模型", "prompt", "提示词", "token", "多模态", "omni", "swiglu", "激活函数"]),
    ("AI 与智能", "AI 智能体", "数据库/服务", ["智能体", "agent", "multi-agent", "多智能体", "aigc", "代理", "框架"]),
    ("AI 与智能", "AI 智能体", "Coze/工作流", ["coze", "工作流", "workbuddy", "象限"]),
    ("AI 与智能", "AI 智能体", "微信/数字员工", ["微信", "数字员工", "数字助理", "whatsapp"]),
    ("AI 与智能", "AI 编程与开发", "Codex/Cursor", ["codex", "cursor", "copilot", "vibe coding", "ai编程", "harness", "浏览器自动化"]),
    ("AI 与智能", "AI 图像/视频生成", "视频生成", ["视频生成", "seedance", "即梦", "pavo", "agnes", "文生视频", "生图", "图像生成", "sora"]),
    ("AI 与智能", "AI 语音/音频", "TTS/语音", ["tts", "语音合成", "语音模型", "配音", "有声", "kokoro", "文本转语音", "语音识别"]),
    ("AI 与智能", "AI 本地部署/开源", "本地模型", ["本地模型", "本地部署", "本地", "部署", "显卡", "离网", "离线"]),
    ("AI 与智能", "AI 效率工具", "自动化", ["工具", "神器", "效率", "干货", "ai技能", "快捷", "自动化"]),
    ("AI 与智能", "AI 行业应用", "金融/量化", ["量化", "交易", "投研", "tradingagents"]),
    ("AI 与智能", "AI 行业应用", "教育/AI 学习", ["ai教育", "ai学习", "ai教师", "ai家教"]),
    ("AI 与智能", "其他", "其他", ["ai", "人工智能", "智能"]),

    # ---------- 编程与开源：二级=用途 ─────
    ("编程与开源", "开发/框架", "Python/JS", ["python", "javascript", "typescript", "js", "代码", "框架", "api", "插件"]),
    ("编程与开源", "开发/框架", "机器学习", ["pytorch", "机器学习", "手写数字", "梯度下降"]),
    ("编程与开源", "开源项目", "GitHub 项目", ["开源", "github", "git", "star", "星标", "开源项目", "仓库"]),
    ("编程与开源", "效率工具", "网站/在线工具", ["网站", "工具", "在线", "文件互传", "互传", "文件传输", "远程工作"]),
    ("编程与开源", "效率工具", "自动化/脚本", ["自动化", "脚本", "办公自动化", "快捷键", "生产力"]),
    ("编程与开源", "数据/部署", "Docker/数据库", ["docker", "部署", "数据库", "服务器", "云服务", "云计算"]),
    ("编程与开源", "GIS/地理位置", "地图/GIS", ["地理信息", "三维地图", "卫星地图", "gis", "webassembly", "地理"]),
    ("编程与开源", "程序员成长", "远程工作/求职", ["程序员", "远程工作", "求职", "外企"]),
    ("编程与开源", "其他", "其他", ["编程", "开发", "码", "技术"]),

    # ---------- 教育与成长：二级=学段/领域 ─────
    ("教育与成长", "英语学习", "启蒙/口语", ["英语启蒙", "口语", "单词", "听力", "big muzzy", "大muzzy", "英语语法", "词汇"]),
    ("教育与成长", "英语学习", "英语语法", ["英语语法", "零基础英语"]),
    ("教育与成长", "数学/理科", "奥数/计算", ["数学", "奥数", "概率论", "统计", "压轴", "物理", "化学"]),
    ("教育与成长", "语文/写作", "写作/汉字", ["作文", "写作", "汉子", "拼音", "阅读", "语文"]),
    ("教育与成长", "考试/升学", "中高考/升学", ["中考", "高考", "升学", "试卷", "阅卷", "报志愿"]),
    ("教育与成长", "学习方法", "记忆/效率", ["记忆", "背", "学习", "复习", "笔记", "提分", "专注力"]),
    ("教育与成长", "育儿/亲子", "亲子/早教", ["育儿", "亲子", "孩子", "父母", "早教", "宝妈"]),
    ("教育与成长", "通识/文化", "历史/文化", ["历史", "文化", "国学", "儒", "诗词", "通史", "唐宋", "明朝", "佛教"]),
    ("教育与成长", "通识/文化", "科普/冷知识", ["科普", "冷知识", "阿拉伯数字", "脑洞", "科学史"]),
    ("教育与成长", "其他", "其他", ["学习", "成长", "知识"]),

    # ---------- 副业与赚钱：二级=模式 ─────
    ("副业与赚钱", "电商/跨境", "亚马逊运营", ["亚马逊", "amazon"]),
    ("副业与赚钱", "电商/跨境", "独立站/跨境电商", ["跨境", "独立站", "外贸", "电商", "选品", "中东", "fordeal"]),
    ("副业与赚钱", "自媒体", "涨粉/内容", ["自媒体", "涨粉", "内容创作", "短视频", "博主", "爆款", "剪辑运营"]),
    ("副业与赚钱", "营销/获客", "营销思维", ["营销", "获客", "获客", "拓客", "地推", "推广", "文案思维", "商业思维", "广告"]),
    ("副业与赚钱", "兼职/项目", "副业项目", ["副业", "兼职", "赚钱", "项目", "挣钱", "摆摊", "信息差"]),
    ("副业与赚钱", "创业/思维", "创业思维", ["创业", "自由职业", "数字游民", "超级个体", "一人公司"]),
    ("副业与赚钱", "其他", "其他", ["生意", "商机", "变现"]),

    # ---------- 生活与健康：二级=主题 ─────
    ("生活与健康", "健康/医疗", "中医/常见病", ["感冒", "风热", "风寒", "医学", "医生", "健康", "养生", "睡眠", "体检", "营养", "中医", "银屑病", "牛皮癣"]),
    ("生活与健康", "护肤/美容", "护肤/祛痘", ["护肤", "痘", "洗面奶", "黑头", "美容", "化妆品", "美妆"]),
    ("生活与健康", "健身/运动", "跑步/燃脂", ["健身", "跑步", "跳绳", "燃脂", "减肥", "瘦身", "瘦", "力量训练", "田径", "运动"]),
    ("生活与健康", "家居/装修", "家电/装修", ["空调", "地暖", "热水", "装修", "家居", "厨宝", "净烟机", "厨房", "窗户", "门窗", "清理"]),
    ("生活与健康", "生活技巧", "省钱/收纳", ["小技巧", "生活技巧", "省钱", "收纳", "家务", "妙招", "改装", "清洁"]),
    ("生活与健康", "其他", "其他", ["生活", "日常"]),

    # ---------- 美食与三农：二级=类型 ─────
    ("美食与三农", "地方美食", "重庆/川渝", ["重庆", "耙牛肉", "小面", "麻辣", "川菜"]),
    ("美食与三农", "地方美食", "面食/小吃", ["火锅", "面", "牛肉", "小吃", "巷子", "探店", "美食", "早餐", "烘焙", "菜"]),
    ("美食与三农", "三农/种植", "种植/农产品", ["三农", "种植", "农产品", "野地瓜", "农民", "花卉", "土特产", "农业", "农村"]),
    ("美食与三农", "其他", "其他", ["吃", "烹饪"]),

    # ---------- 旅行与摄影：二级=类型 ─────
    ("旅行与摄影", "旅行", "周边游/自驾", ["旅行", "自驾", "露营", "户外", "出游", "周边", "京津冀", "河北", "北京", "周末", "涠洲岛", "海岛", "机票", "酒店", "度假", "旅游", "景区", "景点", "阿联酋", "头等舱"]),
    ("旅行与摄影", "摄影/拍照", "人像/风光", ["摄影", "拍照", "相机", "机位", "照片", "人像", "风光", "拍大片"]),
    ("旅行与摄影", "修图/后期", "调色/滤镜", ["调色", "滤镜", "修图", "p图", "轻图"]),
    ("旅行与摄影", "无人机/航拍", "无人机", ["无人机", "航拍"]),
    ("旅行与摄影", "其他", "其他", ["风景", "旅游", "风景"]),

    # ---------- 金融与财经：二级=领域 ─────
    ("金融与财经", "股市/投资", "A股/大盘", ["股票", "a股", "大盘", "收盘", "开盘", "行情", "下周", "指数", "短线"]),
    ("金融与财经", "宏观/政策", "货币/利率", ["逆回购", "降息", "加息", "美联储", "央行", "利率", "信贷", "放贷", "宏观"]),
    ("金融与财经", "理财/房产", "房产/法拍", ["法拍", "房产", "楼市", "房价", "不良资产", "资产处置"]),
    ("金融与财经", "理财/房产", "理财/基金", ["理财", "基金", "投资", "财富"]),
    ("金融与财经", "其他", "其他", ["财经", "金融", "资本市场"]),

    # ---------- 影视娱乐与情感：二级=类型 ─────
    ("影视娱乐与情感", "影视/剧集", "短剧/综艺", ["短剧", "综艺", "电视剧", "剧情", "悬疑", "电影", "国漫"]),
    ("影视娱乐与情感", "音乐/演出", "音乐", ["音乐", "mv", "演唱会", "歌手"]),
    ("影视娱乐与情感", "游戏", "游戏", ["游戏", "使命召唤", "王者", "吃鸡", "掼蛋", "麻将", "斗地主"]),
    ("影视娱乐与情感", "情感/婚恋", "恋爱/婚姻", ["脱单", "恋爱", "追女生", "情感", "相亲", "婚恋", "结婚", "配偶", "老公", "夫妻"]),
    ("影视娱乐与情感", "其他", "其他", ["娱乐", "明星", "网红", "综艺"]),

    # ---------- 设计与办公：二级=类型 ─────
    ("设计与办公", "PPT/演示", "PPT 生成", ["ppt", "演示", "slides", "办" ]),
    ("设计与办公", "平面/图像", "PS/海报", ["设计", "photoshop", "illustrator", "海报", "平面", "排版", "字体", "调色"]),
    ("设计与办公", "视频剪辑", "剪映/PR", ["剪辑", "视频编辑", "剪映", "pr", "渲染", "blender", "3d", "建模"]),
    ("设计与办公", "办公软件", "Word/Excel", ["word", "excel", "wps", "office", "表格", "文档"]),
    ("设计与办公", "其他", "其他", ["素材", "模板"]),
]

def clean_title(raw):
    s = raw or ""
    s = re.sub(r"^([\d.,]+\s*(万|亿)+\s*)", "", s.strip())
    s = re.sub(r"^每周精选内容\s*", "", s)
    s = re.sub(r"^精选\s*", "", s)
    return s.strip()

def classify(r):
    vid = str(r.get("id") or "")
    if vid in OVERRIDES:
        return list(OVERRIDES[vid])
    text = f"{r.get('title','')} {r.get('tags','')} {r.get('text','')}".lower()
    hw = is_hardware_robot(text)
    for l1, l2, l3, kws in RULES:
        if l1 == "智能机器人" and not hw:
            continue
        for kw in kws:
            if kw in text:
                return [l1, l2, l3]
    return ["其他", "其他", "其他"]

def build_tree(records):
    root = {}
    for r in records:
        node = root
        for i, name in enumerate(r["path"]):
            child = node.setdefault(name, {"name": name, "items": [], "children": {}})
            if i == len(r["path"]) - 1:
                child["items"].append(r)
            else:
                node = child["children"]
    def to_n(n):
        items = sorted(n["items"], key=lambda x: x["title"][:10])
        children = [to_n(c) for c in n["children"].values()]
        cnt = len(items) + sum(c["count"] for c in children)
        children.sort(key=lambda x: -x["count"])
        return {"name": n["name"], "count": cnt, "children": children,
                "items": [{"t": it["title"][:60], "u": it["url"], "tags": it["tags"], "full": it["text"]} for it in items]}
    return sorted([to_n(c) for c in root.values()], key=lambda x: -x["count"])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="work/data/favorites.jsonl")
    ap.add_argument("--out", default="outputs/收藏脑图.html")
    ap.add_argument("--csv", default="work/data/cleaned_tree.csv")
    ap.add_argument("--json", default="work/data/cleaned_tree.json")
    args = ap.parse_args()

    infile = Path(args.inp)
    if not infile.exists():
        print("找不到数据文件:", infile); return 1
    seen = {}
    for line in infile.open(encoding="utf-8"):
        line = line.strip()
        if not line: continue
        try: r = json.loads(line)
        except Exception: continue
        if r.get("id") and r["id"] not in seen:
            seen[r["id"]] = r
    records = []
    for vid, r in seen.items():
        title = clean_title(r.get("title", ""))
        text = (r.get("text") or "").strip()
        path = classify(r)
        records.append({"id": vid, "path": path, "title": title or text[:100],
                        "author": (r.get("author") or "").strip(), "tags": r.get("tags") or "",
                        "text": text, "url": r.get("url") or f"https://www.douyin.com/video/{vid}"})

    # 标题去重（抓取串文案导致）
    seen_title = {}; cleaned = []; dup = 0
    for r in records:
        key = r["title"][:40].lower().strip()
        if key in seen_title:
            dup += 1; continue
        seen_title[key] = r; cleaned.append(r)
    records = cleaned
    print(f"[去重] 合并 {dup} 条重复")

    tree = build_tree(records)
    Path(args.json).write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    with Path(args.csv).open("w", encoding="utf-8-sig", newline="") as fc:
        w = csv.writer(fc)
        w.writerow(["id", "一级分类", "二级分类", "三级分类", "标题", "作者", "话题", "链接", "全文"])
        for r in records:
            w.writerow([r["id"], *r["path"], r["title"], r["author"], r["tags"], r["url"], r["text"]])

    html = TEMPLATE.replace("__DATA__", json.dumps(tree, ensure_ascii=False))
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    from collections import Counter
    c1 = Counter(r["path"][0] for r in records)
    print("清洗去重:", len(records))
    print("一级分类:")
    for k, v in c1.most_common():
        print(f"  {k}: {v}")
    print("脑图文件:", out.resolve())
    return 0

if __name__ == "__main__":
    import sys; sys.exit(main())
