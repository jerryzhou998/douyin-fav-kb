#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「需求导向」的收藏脑图：我遇到某个问题时，该翻哪一类。

数据源 data/enriched.json（需求三级分类 + 内容形态 + 可检索术语）。
"""
import json, html, datetime, argparse
from collections import Counter
from pathlib import Path

PIPE = Path(__file__).resolve().parent
DATA = PIPE / "data"

# 一级分类配色（按「需求」而非话题）
COLORS = {
    "AI 编程与智能体": "#2563eb",
    "大模型原理与自建": "#7c3aed",
    "AI 内容创作": "#db2777",
    "工具与资源发现": "#0891b2",
    "办公与文档": "#4f46e5",
    "编程与技术基础": "#0d9488",
    "学习与教育": "#16a34a",
    "赚钱与商业": "#f59e0b",
    "投资与理财": "#b45309",
    "居家与生活": "#65a30d",
    "健康与医疗": "#dc2626",
    "美食与烹饪": "#ea580c",
    "旅行与摄影": "#0284c7",
    "机器人与硬件": "#e11d48",
    "兴趣与休闲": "#8b5cf6",
    "其他": "#64748b",
}
FORM_COLORS = {
    "保姆级教程": "#16a34a", "实战案例": "#2563eb", "工具推荐": "#0891b2",
    "原理讲解": "#7c3aed", "避坑经验": "#dc2626", "资源合集": "#f59e0b",
    "经验分享": "#64748b",
}


def build_tree(rows):
    root = {}
    for r in rows:
        path = r.get("path") or ["其他", "未归类", "待整理"]
        node = root
        for i, name in enumerate(path):
            child = node.setdefault(name, {"name": name, "items": [], "children": {}})
            if i == len(path) - 1:
                child["items"].append(r)
            else:
                node = child["children"]

    def to_n(n):
        items = sorted(n["items"], key=lambda x: -(x.get("chars") or 0))
        children = sorted([to_n(c) for c in n["children"].values()], key=lambda x: -x["count"])
        cnt = len(items) + sum(c["count"] for c in children)
        return {
            "name": n["name"], "count": cnt, "children": children,
            "items": [{
                "t": it.get("title", "")[:90],
                "u": it.get("url", ""),
                "f": it.get("form", ""),
                "k": (it.get("terms") or [])[:6],
                "d": it.get("duration"),
                "c": it.get("chars") or 0,
                "s": it.get("status", ""),
                "r": it.get("_rank"),
                "x": (it.get("transcript") or "")[:180],
            } for it in items],
        }
    return sorted([to_n(c) for c in root.values()], key=lambda x: -x["count"])


TEMPLATE = r"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>抖音收藏 · 需求脑图</title>
<style>
*{box-sizing:border-box}
body{margin:0;font:14px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC","Helvetica Neue",sans-serif;
     background:#f5f6f8;color:#1c1e21;height:100vh;display:flex;flex-direction:column}
header{background:#fff;border-bottom:1px solid #e3e5e8;padding:12px 20px;display:flex;
       align-items:center;gap:14px;flex-wrap:wrap;box-shadow:0 1px 3px rgba(0,0,0,.04);flex-shrink:0}
h1{margin:0;font-size:17px;white-space:nowrap}
.sub{color:#65676b;font-size:12px}
#q{flex:1;min-width:220px;padding:8px 12px;border:1px solid #ccd0d5;border-radius:8px;font-size:14px;outline:none}
#q:focus{border-color:#1877f2}
select{padding:8px 10px;border:1px solid #ccd0d5;border-radius:8px;font-size:13px;background:#fff}
.badge{background:#f0f2f5;color:#65676b;border-radius:20px;padding:4px 12px;font-size:12px;white-space:nowrap}
main{flex:1;display:flex;overflow:hidden;min-height:0}
.left{width:380px;min-width:380px;border-right:1px solid #e3e5e8;overflow:auto;background:#fff;padding:10px 8px}
.right{flex:1;overflow:auto;padding:16px 22px}
.n1,.n2,.n3{display:flex;align-items:center;gap:8px;border-radius:7px;cursor:pointer;user-select:none}
.n1{padding:7px 9px;margin:5px 0 2px;font-weight:700;font-size:14px;color:#fff}
.n1:hover{filter:brightness(1.08)}
.n2{padding:5px 9px 5px 20px;font-weight:600;font-size:13px;color:#3c3c4a}
.n2:hover{background:#eef1ff}
.n3{padding:4px 9px 4px 34px;font-size:12.5px;color:#5a5a6b}
.n3:hover{background:#f2f4ff}
.n3.active,.n2.active{background:#dbe4ff;color:#1a237e;font-weight:600}
.cnt{margin-left:auto;font-size:11px;background:rgba(0,0,0,.10);padding:1px 7px;border-radius:9px;font-variant-numeric:tabular-nums}
.n1 .cnt{background:rgba(255,255,255,.28)}
.arrow{font-size:9px;opacity:.65;width:9px;flex-shrink:0}
.crumb{font-size:13px;color:#65676b;margin-bottom:12px}
.crumb b{color:#1c1e21;font-size:16px}
.card{background:#fff;border:1px solid #e3e5e8;border-radius:9px;padding:11px 14px;margin-bottom:9px;cursor:pointer}
.card:hover{border-color:#1877f2;box-shadow:0 2px 8px rgba(24,119,242,.10)}
.ct{font-weight:600;font-size:14px;margin-bottom:5px;word-break:break-word}
.cm{display:flex;gap:7px;flex-wrap:wrap;align-items:center;font-size:11.5px;color:#65676b}
.tag{padding:1px 8px;border-radius:4px;color:#fff;font-size:11px}
.kw{background:#f0f2f5;color:#4b4f56;padding:1px 8px;border-radius:10px;font-size:11px}
.ex{color:#8a8d91;font-size:12px;margin-top:6px;line-height:1.5;
    display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.path{color:#1877f2;font-size:11.5px}
mark{background:#ffe58f;padding:0 1px;border-radius:2px}
.empty{color:#8a8d91;text-align:center;padding:60px 20px}
.hint{color:#65676b;font-size:13px;background:#fff;border:1px solid #e3e5e8;
      border-radius:9px;padding:14px 16px;line-height:1.8}
.hint b{color:#1c1e21}
@media(max-width:820px){main{flex-direction:column}
  .left{width:100%;min-width:0;max-height:40vh;border-right:none;border-bottom:1px solid #e3e5e8}}
</style></head><body>
<header>
  <h1>🧭 收藏需求脑图</h1>
  <span class="sub">按「遇到问题该翻哪一类」组织</span>
  <input id="q" placeholder="搜索标题 / 术语 / 文案，例如：Skills、MCP、装修避坑">
  <select id="form"><option value="">全部形态</option>__FORMS__</select>
  <span class="badge" id="stat"></span>
</header>
<main>
  <div class="left" id="tree"></div>
  <div class="right" id="panel"></div>
</main>
<script>
const DATA = __DATA__;
const FORM_COLORS = __FORMCOLORS__;
const COLORS = __COLORS__;
const TOTAL = DATA.reduce((a,c)=>a+c.count,0);
let open1={}, open2={}, sel=null;

function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function hl(s,q){ if(!q) return esc(s); const t=String(s||''); const i=t.toLowerCase().indexOf(q.toLowerCase());
  if(i<0) return esc(t); return esc(t.slice(0,i))+'<mark>'+esc(t.slice(i,i+q.length))+'</mark>'+esc(t.slice(i+q.length)); }
function fmt(s){ if(s==null) return ''; s=Math.round(s); return String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0'); }
function col(n){ return COLORS[n]||'#64748b'; }

function allItems(node, path, acc){
  node.items.forEach(it=>acc.push({it, path:path.concat(node.name)}));
  (node.children||[]).forEach(c=>allItems(c, path.concat(node.name), acc));
  return acc;
}
function collect(node){ return allItems(node, [], []); }

function renderTree(){
  const el=document.getElementById('tree'); el.innerHTML='';
  DATA.forEach(n1=>{
    const d1=document.createElement('div'); d1.className='n1'; d1.style.background=col(n1.name);
    d1.innerHTML='<span class="arrow">'+(open1[n1.name]?'▼':'▶')+'</span><span>'+esc(n1.name)+'</span><span class="cnt">'+n1.count+'</span>';
    d1.onclick=()=>{open1[n1.name]=!open1[n1.name]; sel={node:n1,path:[n1.name]}; renderTree(); renderPanel();};
    el.appendChild(d1);
    if(!open1[n1.name]) return;
    (n1.children||[]).forEach(n2=>{
      const key=n1.name+'/'+n2.name;
      const d2=document.createElement('div'); d2.className='n2'+(sel&&sel.key===key?' active':'');
      d2.innerHTML='<span class="arrow">'+((n2.children&&n2.children.length)?(open2[key]?'▼':'▶'):'')+'</span><span>'+esc(n2.name)+'</span><span class="cnt">'+n2.count+'</span>';
      d2.onclick=()=>{open2[key]=!open2[key]; sel={node:n2,path:[n1.name,n2.name],key:key}; renderTree(); renderPanel();};
      el.appendChild(d2);
      if(!open2[key]) return;
      (n2.children||[]).forEach(n3=>{
        const k3=key+'/'+n3.name;
        const d3=document.createElement('div'); d3.className='n3'+(sel&&sel.key===k3?' active':'');
        d3.innerHTML='<span>'+esc(n3.name)+'</span><span class="cnt">'+n3.count+'</span>';
        d3.onclick=()=>{sel={node:n3,path:[n1.name,n2.name,n3.name],key:k3}; renderTree(); renderPanel();};
        el.appendChild(d3);
      });
    });
  });
}

function card(o,q){
  const it=o.it;
  const d=document.createElement('div'); d.className='card';
  const fc=FORM_COLORS[it.f]||'#64748b';
  d.innerHTML='<div class="ct">'+hl(it.t,q)+'</div>'
    +'<div class="cm">'+(it.f?'<span class="tag" style="background:'+fc+'">'+esc(it.f)+'</span>':'')
    +(o.path?'<span class="path">'+esc(o.path.join(' › '))+'</span>':'')
    +(it.r?'<span title="收藏顺序，#1 为最近收藏">收藏#'+it.r+'</span>':'')
    +(it.d?'<span>'+fmt(it.d)+'</span>':'')+(it.c?'<span>'+it.c+'字</span>':'')
    +(it.k||[]).map(k=>'<span class="kw">'+esc(k)+'</span>').join('')+'</div>'
    +(it.x?'<div class="ex">'+hl(it.x,q)+'</div>':'');
  d.onclick=()=>window.open(it.u,'_blank');
  return d;
}

function renderPanel(){
  const p=document.getElementById('panel'); p.innerHTML='';
  const q=document.getElementById('q').value.trim();
  const fm=document.getElementById('form').value;
  let list=[], title='';
  if(q){
    DATA.forEach(n=>collect(n).forEach(o=>list.push(o)));
    const ql=q.toLowerCase();
    list=list.filter(o=>(o.it.t+' '+(o.it.k||[]).join(' ')+' '+(o.it.x||'')).toLowerCase().includes(ql));
    title='搜索「'+q+'」';
  } else if(sel){
    list=collect(sel.node).map(o=>({it:o.it, path:sel.path.slice(1).concat(o.path.slice(1))}));
    title=sel.path.join(' › ');
  } else {
    document.getElementById('stat').textContent='共 '+TOTAL+' 条';
    p.innerHTML='<div class="hint">👈 左侧点开任意分类查看内容。<br><br>'
      +'<b>怎么用：</b>这份脑图按「<b>我遇到什么问题</b>」组织，而不是按话题。<br>'
      +'比如想给 AI 加能力 → <b>AI 编程与智能体 › 能力扩展 › Skills 技能</b>；<br>'
      +'想搭知识库 → <b>大模型原理与自建 › RAG 与知识库</b>。<br><br>'
      +'<b>形态筛选：</b>右上角可只看「保姆级教程」或「避坑经验」。<br>'
      +'<b>搜索：</b>支持标题、术语和文案内容。<br><br>'
      +'卡片上的 <b>收藏#N</b> 是收藏顺序，#1 为最近收藏；<b>收藏文案.html</b> 里可按收藏新旧排序。<br>'
      +'点任意卡片在抖音打开原视频；完整文案见 <b>收藏文案.html</b>。</div>';
    return;
  }
  if(fm) list=list.filter(o=>o.it.f===fm);
  document.getElementById('stat').textContent=list.length+' / '+TOTAL+' 条';
  const c=document.createElement('div'); c.className='crumb'; c.innerHTML='<b>'+esc(title)+'</b> · '+list.length+' 条';
  p.appendChild(c);
  if(!list.length){ p.innerHTML+='<div class="empty">没有匹配的内容</div>'; return; }
  list.forEach(o=>p.appendChild(card(o,q)));
}

let t; document.getElementById('q').addEventListener('input',()=>{clearTimeout(t);t=setTimeout(renderPanel,180)});
document.getElementById('form').addEventListener('change',renderPanel);
renderTree(); renderPanel();
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=str(DATA / "enriched.json"))
    ap.add_argument("--out", default=str(PIPE / "outputs" / "收藏脑图.html"))
    args = ap.parse_args()

    rows = json.loads(Path(args.inp).read_text(encoding="utf-8"))
    fav = DATA / "favorites.jsonl"
    rank = {}
    if fav.exists():
        for pos, line in enumerate(fav.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                fr = json.loads(line)
            except Exception:
                continue
            if fr.get("id") and fr["id"] not in rank:
                rank[fr["id"]] = pos
    for r in rows:
        r["_rank"] = rank.get(r.get("id"))
    tree = build_tree(rows)
    forms = sorted({r.get("form") for r in rows if r.get("form")})

    doc = (TEMPLATE
           .replace("__DATA__", json.dumps(tree, ensure_ascii=False))
           .replace("__FORMCOLORS__", json.dumps(FORM_COLORS, ensure_ascii=False))
           .replace("__COLORS__", json.dumps(COLORS, ensure_ascii=False))
           .replace("__FORMS__", "".join(
               f'<option value="{html.escape(f)}">{html.escape(f)}</option>' for f in forms)))

    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")

    print(f"[需求脑图] {len(rows)} 条 → {out}  ({out.stat().st_size/1024/1024:.1f} MB)")
    for n in tree:
        print(f"  {n['count']:4d}  {n['name']}")
        for c in n["children"][:3]:
            print(f"          └ {c['count']:3d} {c['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
