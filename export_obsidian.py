#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把收藏知识库导出为 Obsidian 仓库（增量、可重复执行）。

结构：
  <vault>/
    首页.md                 总览 + 最新收藏
    分类/<一级分类>.md       每个一级分类一个 MOC（地图式导航）
    视频/<一级分类>/<抖音ID-标题>.md   每个视频一篇笔记（YAML 属性 + 文案）

特性：
  - 文件名用抖音 ID，收藏顺序变化也不会改文件名/断链
  - 内容哈希不变就不重写，保留笔记在 Obsidian 里的修改时间
  - 已失效/被剔除的视频，其旧笔记和空目录自动清理
  - 重新分类导致目录变化时自动搬迁
"""
import argparse, hashlib, json, os, re, sys, datetime
from pathlib import Path

PIPE = Path(__file__).resolve().parent
DATA = PIPE / "data"
ENRICHED = DATA / "enriched.json"
TRANS_DIR = DATA / "transcripts"
FAV = DATA / "favorites.jsonl"

STATUS_CN = {"ok": "已转写", "empty": "无人声", "missing": "待转写", "too_long": "超长跳过"}
MANIFEST_NAME = ".douyin-manifest.json"


def load_fav_rank():
    """收藏顺序：抓取日期倒序（新批次在前），同批次按文件顺序。与脑图/文案页一致。"""
    rows = []
    if FAV.exists():
        for pos, line in enumerate(FAV.read_text(encoding="utf-8").splitlines(), 1):
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
    rank, day = {}, {}
    for i, (fid, d, _) in enumerate(rows, 1):
        rank[fid], day[fid] = i, d
    return rank, day


def q(s):
    """把字符串安全地放进 YAML（双引号、转义）。"""
    return json.dumps(str(s if s is not None else ""), ensure_ascii=False)


def yaml_list(xs):
    return "[" + ", ".join(q(x) for x in xs) + "]"


def safe_name(s, vid):
    s = re.sub(r'[\\/:*?"<>|\[\]#\^\r\n\t]+', " ", s or "")
    s = re.sub(r"\s+", " ", s).strip(" .")[:40]
    return f"{s}-{vid}" if s else vid


def fmt_dur(sec):
    if not sec:
        return ""
    sec = int(round(sec))
    return f"{sec//60:02d}:{sec%60:02d}"


def note_body(r, tr, rank, day):
    vid = r["id"]
    path = r.get("path") or ["其他", "未归类", "待整理"]
    l1, l2, l3 = (path + ["", "", ""])[:3]
    kws = r.get("terms") or r.get("keywords") or []
    pre = r.get("status")
    if pre == "too_long":
        status = "超长跳过"
    elif not tr:
        status = "待转写"
    elif not (tr.get("full_text") or "").strip():
        status = "无人声"
    else:
        status = "已转写"
    full = (tr or {}).get("full_text", "").strip()
    title = (r.get("title") or r.get("text") or vid).strip()

    fm = [
        "---",
        f"标题: {q(title)}",
        f"抖音ID: {q(vid)}",
        f"链接: {r.get('url','')}",
        f"一级分类: {q(l1)}",
        f"二级分类: {q(l2)}",
        f"三级分类: {q(l3)}",
        f"内容形态: {q(r.get('form',''))}",
        f"关键词: {yaml_list(kws)}",
        f"时长: {q(fmt_dur(r.get('duration') or (tr or {}).get('duration')))}",
        f"字数: {len(full)}",
        f"状态: {q(status)}",
        f"收藏序号: {rank.get(vid, '')}",
        f"收录日期: {q(day.get(vid, ''))}",
        "tags:",
        "  - douyin/收藏",
        f"  - douyin/{status}",
        "---",
        "",
    ]
    meta = " · ".join(x for x in [" / ".join(path), r.get("form", ""),
                                 fmt_dur(r.get("duration") or (tr or {}).get("duration")),
                                 f"收藏#{rank[vid]}" if vid in rank else ""] if x)
    body = [f"# {title}", "", f"> {meta}", "",
            f"[▶ 在抖音打开原视频]({r.get('url','')})", "", "## 文案", ""]
    if status == "已转写":
        body.append(full)
    elif status == "无人声":
        body.append("> [!note] 该视频没有识别到人声（纯音乐 / 无旁白）。")
    elif status == "超长跳过":
        body.append("> [!warning] 超长视频，已按设置跳过转写，可点上方链接直接观看。")
    else:
        body.append("> [!todo] 尚未转写，下次运行「2-转写出稿」后自动补全。")
    if kws:
        body += ["", "---", "**可检索术语：** " + " · ".join(f"`{k}`" for k in kws)]
    body += ["", f"*抖音ID: {vid}*", ""]
    return "\n".join(body), status, l1


def wl(rel):
    """Obsidian wikilink（相对仓库根，不含扩展名）。"""
    return f"[[{rel[:-3] if rel.endswith('.md') else rel}]]"


def group_count(groups):
    return sum(len(v) for g in groups.values() for v in g.values())


def main():
    ap = argparse.ArgumentParser()
    default_vault = os.environ.get("DOUYIN_OBSIDIAN_VAULT")
    cfg = DATA / "obsidian_vault.txt"
    if not default_vault and cfg.exists():
        default_vault = cfg.read_text(encoding="utf-8").strip()
    ap.add_argument("--vault", default=default_vault or str(PIPE.parent / "outputs" / "抖音收藏库-Obsidian"))
    args = ap.parse_args()

    vault = Path(args.vault).expanduser()
    rows = json.loads(ENRICHED.read_text(encoding="utf-8"))
    rank, day = load_fav_rank()
    (DATA / "obsidian_vault.txt").write_text(str(vault) + "\n", encoding="utf-8")

    notes_dir = vault / "视频"
    cat_dir = vault / "分类"
    notes_dir.mkdir(parents=True, exist_ok=True)
    cat_dir.mkdir(parents=True, exist_ok=True)

    manifest_p = vault / MANIFEST_NAME
    manifest = json.loads(manifest_p.read_text(encoding="utf-8")) if manifest_p.exists() else {}
    old_paths = {v['path'] if isinstance(v, dict) else v for v in manifest.values()}
    new_paths, bodies, status_count = {}, {}, {"已转写": 0, "无人声": 0, "待转写": 0, "超长跳过": 0}
    cats = {}  # l1 -> l2 -> l3 -> [relpaths]
    for r in rows:
        vid = r["id"]
        tp = TRANS_DIR / f"{vid}.json"
        tr = json.loads(tp.read_text(encoding="utf-8")) if tp.exists() else None
        body, status, l1 = note_body(r, tr, rank, day)
        status_count[status] += 1
        rel = f"视频/{l1}/{safe_name(r.get('title'), vid)}.md"
        bodies[vid] = (rel, body)
        new_paths[vid] = rel
        path = r.get("path") or ["其他", "未归类", "待整理"]
        l2, l3 = (path + ["未归类", "待整理"])[1], (path + ["未归类", "待整理"])[2]
        cats.setdefault(l1, {}).setdefault(l2, {}).setdefault(l3, []).append(rel)

    # 1) 写笔记（内容未变不重写）
    written = skipped = 0
    for vid, (rel, body) in bodies.items():
        fp = vault / rel
        fp.parent.mkdir(parents=True, exist_ok=True)
        h = hashlib.sha1(body.encode("utf-8")).hexdigest()
        if manifest.get(vid, {}).get("h") == h and fp.exists():
            skipped += 1
        else:
            fp.write_text(body, encoding="utf-8")
            written += 1
        manifest[vid] = {"path": rel, "h": h}

    # 2) 清理失效/搬迁后的旧文件与空目录
    live = set(new_paths.values())
    for rel in old_paths - live:
        fp = vault / rel
        if fp.exists():
            fp.unlink()
    for d in sorted(notes_dir.rglob("*"), reverse=True):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    # 只保留当前分类的 MOC
    keep_cats = {f"分类/{l1}.md" for l1 in cats}
    for f in cat_dir.glob("*.md"):
        if f"分类/{f.name}" not in keep_cats:
            f.unlink()

    # 3) 分类 MOC
    for l1, groups in sorted(cats.items(), key=lambda kv: -group_count(kv[1])):
        lines = [f"# {l1}", "",
                 f"共 **{sum(len(v) for g in groups.values() for v in g.values())}** 条收藏。",
                 f"[[首页|← 返回首页]]", ""]
        for l2 in sorted(groups, key=lambda k: -sum(len(v) for v in groups[k].values())):
            lines.append(f"## {l2}")
            for l3 in sorted(groups[l2], key=lambda k: -len(groups[l2][k])):
                links = groups[l2][l3]
                lines.append(f"- **{l3}**（{len(links)}）：" +
                             "、".join(wl(x) for x in links[:12]) +
                             (f" 等 {len(links)} 条" if len(links) > 12 else ""))
            lines.append("")
        (cat_dir / f"{l1}.md").write_text("\n".join(lines), encoding="utf-8")

    # 4) 首页
    total = len(rows)
    latest = sorted(rows, key=lambda r: rank.get(r["id"], 9e9))[:30]
    h = ["---", "tags: [douyin/首页]", "---", "",
         "# 📚 抖音收藏知识库", "",
         f"共 **{total}** 条 ｜ ✅ 已转写 {status_count['已转写']} "
         f"｜ 🔇 无人声 {status_count['无人声']} ｜ ⏭️ 超长跳过 {status_count['超长跳过']} "
         f"｜ ⏳ 待转写 {status_count['待转写']}", "",
         f"*最近同步：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}*", "",
         "## 🗂 按需求分类", ""]
    for l1 in sorted(cats, key=lambda k: -group_count(cats[k])):
        n = sum(len(v) for g in cats[l1].values() for v in g.values())
        h.append(f"- [[分类/{l1}|{l1}]]（{n}）")
    h += ["", "## 🆕 最新收藏（前 30 条）", ""]
    for r in latest:
        rel = new_paths[r["id"]]
        st = {v: k for k, v in STATUS_CN.items()}
        s = ""
        tp = TRANS_DIR / f"{r['id']}.json"
        if not tp.exists():
            s = " ⏳"
        elif not json.loads(tp.read_text(encoding='utf-8')).get("full_text", "").strip():
            s = " 🔇"
        form = f"_{r['form']}_ · " if r.get("form") else ""
        h.append(f"{rank.get(r['id'],'')}. {wl(rel)}{s} — {form}{(r.get('path') or [''])[0]}")
    h += ["", "> 每次运行「1-抓取收藏」或「2-转写出稿」后，本仓库自动增量更新。", ""]
    (vault / "首页.md").write_text("\n".join(h), encoding="utf-8")

    manifest_p.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    print(f"[Obsidian] 仓库：{vault}")
    print(f"  笔记 {total} 篇（新写/改写 {written}，未变 {skipped}）"
          f"｜ 已转写 {status_count['已转写']}，待转写 {status_count['待转写']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
