#!/usr/bin/env python3
"""抖音收藏一键抓取 v4
要点：
1) 全页面扫描可滚动容器，挑出“包含视频链接的那个”，内部逐段滚动；
2) 同时拦截抖音数据接口(aweme API)；
3) 支持断点续抓，进度实时写入 favorites.jsonl / favorites.csv / debug.log。
"""
import argparse, csv, json, os, re, sys, time, datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

EXTRACT_JS = r"""
() => {
  const out = [];
  const urlre = /\/video\/(\d+)/;
  const links = Array.from(document.querySelectorAll('a[href*=video]'));
  for (const a of links) {
    const href = a.getAttribute('href') || '';
    const m = href.match(urlre);
    if (!m) continue;
    const id = m[1];
    let card = a, text = (a.innerText || '').replace(/\s+/g, ' ').trim();
    for (let i = 0; i < 6; i++) {
      if (!card || card === document.body) break;
      const t = (card.innerText || '').replace(/\s+/g, ' ').trim();
      if (t.length > text.length) text = t;
      if (t.length > 12) break;
      const p = card.parentElement;
      if (!p || p === document.body) break;
      // 防止一路爬到整个列表容器：容器里有不止一个视频链接就停，避免文案串卡
      if (p.querySelectorAll('a[href*="/video/"]').length > 1) break;
      card = p;
    }
    const tags = [];
    for (const tm of (text.matchAll(/#[^\s#]+/g) || [])) tags.push(tm[0].replace(/^#/, ''));
    out.push({ id, url: 'https://www.douyin.com/video/' + id, text, tags: tags.join('，') });
  }
  const seen = new Set();
  const uniq = [];
  for (const r of out) { if (!seen.has(r.id)) { seen.add(r.id); uniq.push(r); } }
  return uniq;
}
"""

# 全页面扫描：找出所有可滚动且包含视频链接的容器
SCROLL_INFO_JS = r"""
() => {
  const all = document.querySelectorAll('*');
  const out = [];
  for (const el of all) {
    const sh = el.scrollHeight, ch = el.clientHeight;
    if (!(sh > ch + 40 && ch > 150)) continue;
    const cs = window.getComputedStyle(el);
    if (!['auto', 'scroll', 'overlay'].includes(cs.overflowY)) continue;
    if (!el.querySelector('a[href*="/video/"]')) continue;
    out.push({
      tag: el.tagName, cls: String(el.className || '').slice(0, 100), id: el.id || '',
      sh, ch, top: Math.round(el.getBoundingClientRect().top),
    });
  }
  out.sort((a, b) => b.sh - a.sh);
  return out.slice(0, 8);
}
"""

SCROLL_ACTION_JS = r"""
() => {
  const all = document.querySelectorAll('*');
  const cands = [];
  for (const el of all) {
    const sh = el.scrollHeight, ch = el.clientHeight;
    if (!(sh > ch + 40 && ch > 150)) continue;
    const cs = window.getComputedStyle(el);
    if (!['auto', 'scroll', 'overlay'].includes(cs.overflowY)) continue;
    if (!el.querySelector('a[href*="/video/"]')) continue;
    cands.push(el);
  }
  cands.sort((a, b) => b.scrollHeight - a.scrollHeight);
  const target = cands.length ? cands[0] : null;
  let moved = 0;
  let atEnd = false;
  if (target) {
    const step = Math.max(900, Math.round(target.clientHeight * 0.8));
    target.scrollTop += step;
    moved = 1;
    atEnd = target.scrollTop + target.clientHeight >= target.scrollHeight - 60;
  }
  window.scrollBy(0, 900);
  return { moved, atEnd, picked: target ? target.tagName + '#' + (target.id||'') : 'none',
           sh: target ? target.scrollHeight : 0, top: target ? target.scrollTop : 0,
           ch: target ? target.clientHeight : 0 };
}
"""

def extract_item(obj, out):
    if isinstance(obj, dict):
        if (obj.get("aweme_id") or obj.get("awemeId")) and (obj.get("desc") or obj.get("video")):
            out.append(obj)
        for v in obj.values():
            extract_item(v, out)
    elif isinstance(obj, list):
        for v in obj:
            extract_item(v, out)

def api_to_record(item):
    try:
        aid = str(item.get("aweme_id") or item.get("awemeId") or "").split(".")[0]
        desc = str(item.get("desc") or "").strip()
        author = ""
        au = item.get("author") or {}
        if isinstance(au, dict):
            author = str(au.get("nickname") or au.get("uid") or "").strip()
        tags = [t.strip("#") for t in re.findall(r"#([^\s#，,]+)", desc)]
        return {"id": aid, "url": "https://www.douyin.com/video/" + aid,
                "title": desc[:200], "text": desc, "author": author,
                "tags": "，".join(tags), "source": "api",
                "found_at": datetime.datetime.now().isoformat(timespec="seconds")}
    except Exception:
        return None

def clean_default(r):
    text = re.sub(r"[ \t]+", " ", r.get("text", "")).strip()
    tags = re.split(r"[，,]", r.get("tags", ""))
    tags = [t.strip() for t in tags if t.strip()]
    return {"id": r["id"], "url": r["url"], "title": text[:200], "text": text,
            "author": r.get("author", ""), "tags": "，".join(tags),
            "found_at": datetime.datetime.now().isoformat(timespec="seconds")}

def load_seen(jsonl):
    seen = set()
    if jsonl.exists():
        for line in jsonl.open(encoding="utf-8"):
            line = line.strip()
            if not line: continue
            try: seen.add(json.loads(line)["id"])
            except Exception: pass
    return seen

def write_csv(jsonl, csvp):
    seen = set(); rows = []
    if jsonl.exists():
        for line in jsonl.open(encoding="utf-8"):
            line = line.strip()
            if not line: continue
            try:
                r = json.loads(line)
                if r["id"] in seen: continue
                seen.add(r["id"]); rows.append(r)
            except Exception: pass
    with csvp.open("w", encoding="utf-8-sig", newline="") as fc:
        w = csv.writer(fc)
        w.writerow(["id", "title", "author", "tags", "url", "text"])
        for r in rows:
            w.writerow([r["id"], r["title"], r.get("author", ""), r.get("tags", ""), r["url"], r["text"]])
    return rows

def log(fh, msg):
    line = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line)
    try: fh.write(line + "\n"); fh.flush()
    except Exception: pass

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=os.path.expanduser("~/.codex-douyin-profile"))
    ap.add_argument("--out", default="work/data")
    ap.add_argument("--max-scrolls", type=int, default=15000)
    ap.add_argument("--incremental", action="store_true",
                    help="增量模式：连续遇到已抓过的旧视频就提前停止")
    ap.add_argument("--stop-after-known", type=int, default=40,
                    help="增量模式下，连续遇到多少条已知旧视频就停止")
    ap.add_argument("--url", default="https://www.douyin.com/")
    args = ap.parse_args()

    outdir = Path(args.out); outdir.mkdir(parents=True, exist_ok=True)
    jsonl = outdir / "favorites.jsonl"
    csvp = outdir / "favorites.csv"
    deb = outdir / "debug.log"
    seen = load_seen(jsonl)

    with deb.open("a", encoding="utf-8") as fh:
        log(fh, "=" * 60)
        log(fh, f"启动续抓 v4，已有存档 {len(seen)} 条")
        t0 = time.time()
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=args.profile, channel="chrome", headless=False,
                viewport={"width": 1440, "height": 950},
                ignore_default_args=["--enable-automation"])
            page = context.new_page()
            page.set_default_timeout(25000)

            api_items = []
            def on_response(resp):
                try:
                    url = resp.url
                    if not (url.startswith("https://www.douyin.com") or url.startswith("https://aweme.snssdk.com")) or "aweme/v1" not in url:
                        return
                    try:
                        ct = resp.headers.get("content-type", "")
                        if "json" not in ct:
                            return
                        data = resp.json()
                    except Exception:
                        return
                    tmp = []
                    extract_item(data, tmp)
                    for it in tmp:
                        rec = api_to_record(it)
                        if rec and rec["id"]:
                            api_items.append(rec)
                except Exception:
                    pass
            page.on("response", on_response)

            log(fh, "打开抖音…")
            try:
                page.goto(args.url, wait_until="domcontentloaded")
            except Exception as e:
                log(fh, f"打开抖音超时: {e}")
            page.wait_for_timeout(3000)
            log(fh, "请在 Chrome 进入『我的收藏』→『视频』页，然后回终端按回车。")
            input("准备好请按回车：")

            page.bring_to_front()
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(4000)

            # 初次诊断容器
            try:
                info = page.evaluate(SCROLL_INFO_JS)
                short = info[0] if info else None
                if short:
                    log(fh, f"已定位滚动容器: {short['tag']}#{short['id']} {short['cls']} scrollH={short['sh']} clientH={short['ch']}")
                else:
                    log(fh, "警告：未发现可滚动容器（请确认已进入收藏的视频列表）")
            except Exception as e:
                log(fh, f"容器诊断失败: {e}")

            processed_api = 0
            total_new = 0
            last_new_round = 0
            known_streak = 0          # 连续遇到旧视频的条数
            hit_known_limit = False
            if args.incremental:
                log(fh, f"增量模式：已有 {len(seen)} 条存档，连续遇到 {args.stop_after_known} 条旧视频即停止")
            info_snapshot = None
            with jsonl.open("a", encoding="utf-8") as fj:
                for round_ in range(1, args.max_scrolls + 1):
                    # 1) 接口数据
                    n_api = 0
                    for rec in api_items[processed_api:]:
                        if rec["id"] not in seen:
                            seen.add(rec["id"]); total_new += 1; n_api += 1
                            known_streak = 0
                            fj.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        elif args.incremental:
                            known_streak += 1
                    processed_api = len(api_items)

                    # 2) DOM 兜底
                    added_dom = 0
                    try:
                        rows = page.evaluate(EXTRACT_JS)
                    except Exception:
                        rows = []
                    for r in rows:
                        if r["id"] in seen:
                            if args.incremental:
                                known_streak += 1
                            continue
                        rec = clean_default(r)
                        seen.add(rec["id"]); added_dom += 1; total_new += 1
                        known_streak = 0
                        fj.write(json.dumps(rec, ensure_ascii=False) + "\n")

                    if n_api or added_dom:
                        last_new_round = round_
                        write_csv(jsonl, csvp)
                        log(fh, f"第{round_}轮：接口+{n_api}，页面+{added_dom}，累计 {len(seen)} 条")

                    # 3) 滚动正确的内嵌容器
                    try:
                        info_snapshot = page.evaluate(SCROLL_INFO_JS)
                        act = page.evaluate(SCROLL_ACTION_JS)
                        # 鼠标滚轮辅助触发
                        try:
                            b = page.locator('a[href*="/video/"]').first.bounding_box()
                            if b:
                                page.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
                                page.mouse.wheel(0, 900)
                        except Exception:
                            pass
                        page.wait_for_timeout(1300)
                    except Exception as e:
                        act = {"moved": 1, "atEnd": False}
                        log(fh, f"滚动异常: {e}")

                    stuck_end = bool(act.get("atEnd")) and not bool(act.get("moved"))
                    if round_ % 8 == 0 or (not info_snapshot):
                        pin = info_snapshot[0] if info_snapshot else None
                        log(fh, f"第{round_}轮 容器={'有' if pin else '无'} "
                                f"scrollH={pin['sh'] if pin else '-'} top={act.get('top')} "
                                f"滚动容器选中={act.get('picked')} 接口数={len(api_items)}")

                    if args.incremental and known_streak >= args.stop_after_known:
                        hit_known_limit = True
                        log(fh, f"增量模式：连续 {known_streak} 条均为已抓过的旧视频，"
                                f"判定新内容已抓完，提前停止。本次新增 {total_new} 条")
                        break

                    rounds_since_new = round_ - last_new_round
                    if stuck_end and rounds_since_new >= 40 and len(seen) > 20:
                        log(fh, f"滚动到内嵌容器底部且 {rounds_since_new} 轮无新增，停止。共 {len(seen)} 条")
                        break
                    if rounds_since_new >= 120:
                        log(fh, f"已 {rounds_since_new} 轮无新增，停止保护。共 {len(seen)} 条")
                        break

            context.close()

        rows = write_csv(jsonl, csvp)
        dt = time.time() - t0
        log(fh, "=" * 60)
        log(fh, f"结束：共 {len(rows)} 条收藏，本次新增 {total_new} 条，接口捕获 {len(api_items)} 条，耗时 {dt/60:.1f} 分钟")
        log(fh, f"数据文件: {jsonl.resolve()}")
        return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n用户停止。已抓内容已存档，可再次运行续抓。")
        sys.exit(130)
    except Exception:
        import traceback; traceback.print_exc(); sys.exit(1)
