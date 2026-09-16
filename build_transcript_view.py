#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 701 条收藏 + 语音转写文案合成一个可搜索的 HTML 页面 + 一份 CSV。"""
import json, csv, html, datetime
from pathlib import Path

PIPE = Path(__file__).resolve().parent
OUT = PIPE / "outputs"
ENRICHED = PIPE / "data" / "enriched.json"
CLEANED = PIPE / "data" / "cleaned_tree.json"
ROWS = json.loads((ENRICHED if ENRICHED.exists() else CLEANED).read_text(encoding="utf-8"))
TRANS_DIR = PIPE / "data" / "transcripts"
FAV = PIPE / "data" / "favorites.jsonl"
def load_fav_meta(path):
    """从 favorites.jsonl 计算收藏顺序。

    抖音收藏页按收藏时间倒序（最新在前），抓取时自上而下写入文件；
    增量补抓时新收藏出现在页面顶部，但追加在文件末尾。
    因此真实顺序 = 抓取日期倒序（新批次在前），同批次内保持文件顺序。
    """
    rows = []
    if path.exists():
        for pos, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                fr = json.loads(line)
            except Exception:
                continue
            if fr.get("id"):
                rows.append((fr["id"], (fr.get("found_at") or "")[:10], pos))
    rows.sort(key=lambda x: (-int(x[1].replace("-", "") or 0), x[2]))
    return {fid: {"rank": i, "at": day} for i, (fid, day, _) in enumerate(rows, 1)}
fav_meta = load_fav_meta(FAV)

def fmt_ts(sec):
    if sec is None:
        return ""
    s = int(sec); return f"{s//60:02d}:{s%60:02d}"

items = []
for r in ROWS:
    vid = r["id"]
    tp = TRANS_DIR / f"{vid}.json"
    tr = json.loads(tp.read_text(encoding="utf-8")) if tp.exists() else None
    full = (tr or {}).get("full_text", "").strip()
    pre = r.get("status")
    if pre == "too_long":
        status = "too_long"     # 超长视频，按设置跳过
    elif tr is None:
        status = "missing"      # 尚未转写/无法下载
    elif not full:
        status = "empty"        # 无人声/纯音乐
    else:
        status = "ok"
    items.append({
        "id": vid,
        "title": (r.get("title") or r.get("text") or "").strip(),
        "cat": " / ".join(r.get("path") or []),
        "url": r.get("url", ""),
        "tags": r.get("tags", ""),
        "duration": (tr or {}).get("duration"),
        "chars": len(full),
        "status": status,
        "text": full,
        "keywords": r.get("terms") or r.get("keywords") or [],
        "form": r.get("form", ""),
        "l1": (r.get("path") or ["其他"])[0],
        "note": r.get("note", ""),
        "segments": (tr or {}).get("segments") or [],
        "rank": fav_meta.get(vid, {}).get("rank"),
        "fav_at": fav_meta.get(vid, {}).get("at", ""),
    })

OUT.mkdir(parents=True, exist_ok=True)

# ---------- CSV ----------
csv_path = OUT / "收藏文案.csv"
with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["序号", "需求分类", "内容形态", "标题", "可检索术语", "时长(秒)", "字数", "状态", "链接", "文案"])
    for i, it in enumerate(items, 1):
        st = {"ok": "已转写", "empty": "无人声", "missing": "待处理", "too_long": "超长跳过"}[it["status"]]
        w.writerow([i, it["cat"], it["form"], it["title"], "、".join(it["keywords"]),
                    it["duration"] or "", it["chars"], st, it["url"], it["text"]])

# ---------- TXT ----------
txt_path = OUT / "收藏文案.txt"
with txt_path.open("w", encoding="utf-8") as f:
    for i, it in enumerate(items, 1):
        f.write(f"{'='*70}\n[{i}] {it['title']}\n分类：{it['cat']}\n链接：{it['url']}\n")
        if it["keywords"]:
            f.write(f"关键词：{'、'.join(it['keywords'])}\n")
        if it["status"] == "too_long":
            f.write(f"（{it['note']}）\n\n")
        elif it["status"] == "missing":
            f.write("（尚未转写）\n\n")
        elif it["status"] == "empty":
            f.write("（该视频无人声/纯音乐）\n\n")
        else:
            f.write(f"\n{it['text']}\n\n")

# ---------- HTML ----------
cats = sorted({it["cat"].split(" / ")[0] for it in items if it["cat"]})
forms = sorted({it["form"] for it in items if it["form"]})
data_json = json.dumps(items, ensure_ascii=False)
n_ok = sum(1 for i in items if i["status"] == "ok")
n_empty = sum(1 for i in items if i["status"] == "empty")
n_missing = sum(1 for i in items if i["status"] == "missing")
n_long = sum(1 for i in items if i["status"] == "too_long")
built = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

html_doc = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>抖音收藏 · 视频文案库</title>
<style>
*{box-sizing:border-box}
body{margin:0;font:15px/1.7 -apple-system,BlinkMacSystemFont,"PingFang SC","Helvetica Neue",sans-serif;background:#f5f6f8;color:#1c1e21}
header{position:sticky;top:0;z-index:10;background:#fff;border-bottom:1px solid #e3e5e8;padding:14px 20px;box-shadow:0 1px 3px rgba(0,0,0,.04)}
h1{margin:0 0 10px;font-size:19px}
.stats{color:#65676b;font-size:13px;margin-bottom:10px}
.stats b{color:#1c1e21}
.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
input[type=search]{flex:1;min-width:240px;padding:9px 13px;border:1px solid #ccd0d5;border-radius:8px;font-size:14px;outline:none}
input[type=search]:focus{border-color:#1877f2}
select{padding:9px 11px;border:1px solid #ccd0d5;border-radius:8px;font-size:14px;background:#fff}
main{max-width:1000px;margin:18px auto;padding:0 16px}
.card{background:#fff;border:1px solid #e3e5e8;border-radius:10px;margin-bottom:12px;overflow:hidden}
.card-head{padding:13px 16px;cursor:pointer;display:flex;gap:12px;align-items:flex-start}
.card-head:hover{background:#f7f8fa}
.idx{color:#8a8d91;font-size:13px;min-width:38px;font-variant-numeric:tabular-nums}
.head-main{flex:1;min-width:0}
.title{font-weight:600;margin-bottom:4px;word-break:break-word}
.meta{font-size:12px;color:#65676b;display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.cat{background:#e7f3ff;color:#1877f2;padding:1px 7px;border-radius:4px}
.form{background:#e8f5e9;color:#2e7d32;padding:1px 7px;border-radius:4px}
.badge{padding:1px 7px;border-radius:4px;font-size:11px}
.b-empty{background:#fff3cd;color:#8a6d00}
.b-missing{background:#ffe0e0;color:#c62828}
.b-long{background:#e8e0ff;color:#5b21b6}
.kw{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}
.kw span{background:#f0f2f5;color:#4b4f56;font-size:11px;padding:2px 8px;border-radius:10px}
.body{display:none;padding:0 16px 16px 66px;border-top:1px solid #f0f1f3}
.card.open .body{display:block}
.card.open .card-head{background:#f7f8fa}
.text{white-space:pre-wrap;word-break:break-word;background:#fafbfc;border:1px solid #eceef0;border-radius:8px;padding:13px;margin:12px 0;max-height:460px;overflow:auto}
.seg{display:flex;gap:10px;padding:2px 0;font-size:14px}
.t{color:#1877f2;font-variant-numeric:tabular-nums;min-width:48px;cursor:default}
.acts{display:flex;gap:8px;flex-wrap:wrap}
.btn{padding:6px 12px;border:1px solid #ccd0d5;background:#fff;border-radius:7px;font-size:13px;cursor:pointer;text-decoration:none;color:#1c1e21}
.btn:hover{background:#f0f1f3}
.btn-p{background:#1877f2;color:#fff;border-color:#1877f2}
.btn-p:hover{background:#166fe0}
.hint{color:#65676b;font-size:13px}
mark{background:#ffe58f;padding:0 1px}
.empty-note{color:#8a6d00;font-size:14px;padding:10px 0}
#none{display:none;text-align:center;color:#65676b;padding:50px 0}
.toggle-seg{font-size:12px;color:#1877f2;cursor:pointer;user-select:none}
</style></head><body>
<header>
  <h1>抖音收藏 · 视频文案库</h1>
  <div class="stats">共 <b>__TOTAL__</b> 条 ｜ 已转写 <b>__OK__</b> ｜ 无人声 <b>__EMPTY__</b> ｜ 超长跳过 <b>__LONG__</b> ｜ 待处理 <b>__MISSING__</b> ｜ 生成于 __BUILT__ ｜ 序号 = 收藏顺序，#1 为最近收藏</div>
  <div class="controls">
    <input type="search" id="q" placeholder="搜索标题 / 关键词 / 文案内容，例如：提示词缓存 / 收纳 / DeepSeek">
    <select id="cat"><option value="">全部分类</option>__CATS__</select>
    <select id="form"><option value="">全部形态</option>__FORMS__</select>
    <select id="st">
      <option value="">全部状态</option>
      <option value="ok">已转写</option>
      <option value="empty">无人声</option>
      <option value="too_long">超长跳过</option>
      <option value="missing">待处理</option>
    </select>
    <select id="sort">
      <option value="new">收藏顺序：新 → 旧</option>
      <option value="old">收藏顺序：旧 → 新</option>
      <option value="chars">文案字数：多 → 少</option>
    </select>
    <button class="btn" id="expand">展开全部</button>
  </div>
</header>
<main><div id="list"></div><div id="none">没有匹配的结果</div></main>
<script>
const DATA = __DATA__;
const list = document.getElementById('list');
const q = document.getElementById('q');
const catSel = document.getElementById('cat');
const stSel = document.getElementById('st');
const formSel = document.getElementById('form');
const sortSel = document.getElementById('sort');
let expanded = false;

function esc(s){return s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function hl(s,kw){ if(!kw) return esc(s);
  const i = s.toLowerCase().indexOf(kw.toLowerCase());
  if(i<0) return esc(s);
  return esc(s.slice(0,i))+'<mark>'+esc(s.slice(i,i+kw.length))+'</mark>'+esc(s.slice(i+kw.length));
}
function fmt(sec){ if(sec==null) return ''; const s=Math.round(sec); return String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0'); }

function render(){
  const kw = q.value.trim();
  const cat = catSel.value, st = stSel.value, fm = formSel.value;
  const kwl = kw.toLowerCase();
  let html = '', n = 0;
  const sv = sortSel.value;
  let arr = DATA.map((it, i) => ({it: it, i: i}));
  if(sv === 'old') arr.sort((a, b) => (b.it.rank || 9e9) - (a.it.rank || 9e9));
  else if(sv === 'chars') arr.sort((a, b) => (b.it.chars || 0) - (a.it.chars || 0));
  else arr.sort((a, b) => (a.it.rank || 9e9) - (b.it.rank || 9e9));
  arr.forEach(({it, i}) => {
    if(cat && !it.cat.startsWith(cat)) return;
    if(st && it.status !== st) return;
    if(fm && it.form !== fm) return;
    if(kw && !(it.title.toLowerCase().includes(kwl) || it.text.toLowerCase().includes(kwl)
        || (it.keywords||[]).join(' ').toLowerCase().includes(kwl))) return;
    n++;
    let badge = '';
    if(it.status==='empty') badge = '<span class="badge b-empty">无人声</span>';
    if(it.status==='missing') badge = '<span class="badge b-missing">待处理</span>';
    if(it.status==='too_long') badge = '<span class="badge b-long">超长跳过</span>';
    let body;
    if(it.status==='too_long'){
      body = '<div class="empty-note">'+esc(it.note||'超长视频，已跳过转写')+'</div>'
           + '<div class="acts"><a class="btn" href="'+it.url+'" target="_blank">打开抖音链接</a></div>';
    } else if(it.status==='missing'){
      body = '<div class="empty-note">尚未转写（下次运行会自动补上）。</div>'
           + '<div class="acts"><a class="btn" href="'+it.url+'" target="_blank">打开抖音链接</a></div>';
    } else if(it.status==='empty'){
      body = '<div class="empty-note">这条视频没有识别到人声（纯音乐/无旁白）。</div>'
           + '<div class="acts"><a class="btn" href="'+it.url+'" target="_blank">打开抖音链接</a></div>';
    } else {
      let excerpt = it.text;
      if(kw){ const p = it.text.toLowerCase().indexOf(kwl);
        if(p>200){ excerpt = '…'+it.text.slice(p-150); } }
      body = '<div class="text" data-full="1">'+hl(excerpt,kw)+'</div>'
        + '<div class="acts">'
        + '<button class="btn btn-p" data-copy="'+i+'">复制文案</button>'
        + '<button class="btn" data-seg="'+i+'">显示时间轴</button>'
        + '<a class="btn" href="'+it.url+'" target="_blank">打开抖音</a>'
        + '</div><div class="segbox" id="seg'+i+'" style="display:none"></div>';
    }
    html += '<div class="card'+(expanded?' open':'')+'" data-i="'+i+'">'
      + '<div class="card-head"><div class="idx">'+(it.rank || (i+1))+'</div><div class="head-main">'
      + '<div class="title">'+hl(it.title||'(无标题)',kw)+'</div>'
      + '<div class="meta">'+(it.cat?'<span class="cat">'+esc(it.cat)+'</span>':'')
      + (it.form?'<span class="form">'+esc(it.form)+'</span>':'')
      + (it.fav_at?'<span>收录 '+it.fav_at+'</span>':'')
      + (it.duration?'<span>'+fmt(it.duration)+'</span>':'')
      + (it.chars?'<span>'+it.chars+'字</span>':'')+badge+'</div>'
      + (it.keywords&&it.keywords.length?'<div class="kw">'+it.keywords.map(k=>'<span>'+esc(k)+'</span>').join('')+'</div>':'')
      + '</div></div><div class="body">'+body+'</div></div>';
  });
  list.innerHTML = html;
  document.getElementById('none').style.display = n ? 'none' : 'block';
}

list.addEventListener('click', e => {
  const copyBtn = e.target.closest('[data-copy]');
  if(copyBtn){ e.stopPropagation();
    navigator.clipboard.writeText(DATA[+copyBtn.dataset.copy].text)
      .then(()=>{copyBtn.textContent='已复制 ✓'; setTimeout(()=>copyBtn.textContent='复制文案',1500)});
    return; }
  const segBtn = e.target.closest('[data-seg]');
  if(segBtn){ e.stopPropagation();
    const i = +segBtn.dataset.seg, box = document.getElementById('seg'+i);
    if(box.style.display==='none'){
      box.innerHTML = '<div class="text">'+DATA[i].segments.map(s=>
        '<div class="seg"><span class="t">'+fmt(s.start)+'</span><span>'+esc(s.text)+'</span></div>').join('')+'</div>';
      box.style.display='block'; segBtn.textContent='隐藏时间轴';
    } else { box.style.display='none'; segBtn.textContent='显示时间轴'; }
    return; }
  const head = e.target.closest('.card-head');
  if(head) head.parentElement.classList.toggle('open');
});

document.getElementById('expand').addEventListener('click', ()=>{
  expanded = !expanded;
  document.getElementById('expand').textContent = expanded?'收起全部':'展开全部';
  render();
});
let timer; q.addEventListener('input', ()=>{clearTimeout(timer); timer=setTimeout(render,180)});
catSel.addEventListener('change', render); stSel.addEventListener('change', render);
sortSel.addEventListener('change', render);
formSel.addEventListener('change', render);
render();
</script></body></html>"""

html_doc = (html_doc
    .replace("__TOTAL__", str(len(items)))
    .replace("__OK__", str(n_ok))
    .replace("__EMPTY__", str(n_empty))
    .replace("__MISSING__", str(n_missing))
    .replace("__LONG__", str(n_long))
    .replace("__BUILT__", built)
    .replace("__CATS__", "".join(f'<option value="{html.escape(c)}">{html.escape(c)}</option>' for c in cats))
    .replace("__FORMS__", "".join(f'<option value="{html.escape(c)}">{html.escape(c)}</option>' for c in forms))
    .replace("__DATA__", data_json))

html_path = OUT / "收藏文案.html"
html_path.write_text(html_doc, encoding="utf-8")

print(f"共 {len(items)} 条：已转写 {n_ok}，无人声 {n_empty}，超长跳过 {n_long}，待处理 {n_missing}")
print("已生成：")
for p in (html_path, csv_path, txt_path):
    print(" -", p, f"({p.stat().st_size/1024/1024:.1f} MB)")
