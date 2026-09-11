#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完整流程：下载全部音频 + AI 语音转文字（断点续跑）
用法: python transcribe_pipeline.py [--limit N] [--ids ...] [--model small]
运行说明：
  - 请先保持专用 Chrome 开着并已登录抖音（用于导出下载凭证）
  - 每个 mp3 只在缺的时候下载；每个视频只在未转好时转写
  - 中途随时 Ctrl+C，下次再跑会接着来，不重复
"""
import argparse, json, os, subprocess, sys, time, datetime
from pathlib import Path
import urllib.request
import urllib.parse
from pipeline_common import aweme_detail, video_minutes, load_state, save_state

PIPE_DIR = Path(__file__).resolve().parent
DATA = PIPE_DIR / "data" / "cleaned_tree.json"
AUDIO_DIR = PIPE_DIR / "audio"
TRANS_DIR = PIPE_DIR / "data" / "transcripts"
COOKIE_FILE = PIPE_DIR / "cookies.txt"
LOG_FILE = PIPE_DIR / "transcribe.log"
CDP = "http://127.0.0.1:9222"
YDL = PIPE_DIR / ".venv/bin/yt-dlp"
PROFILE = os.path.expanduser("~/.codex-douyin-profile")

def log(msg):
    line = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def write_cookies(ctx):
    cookies = ctx.cookies()
    lines = ["# Netscape HTTP Cookie File"]
    for c in cookies:
        dom = c.get("domain", "")
        if "douyin" not in dom and "amemv" not in dom:
            continue
        inc = "TRUE" if dom.startswith(".") else "FALSE"
        secure = "TRUE" if c.get("secure") else "FALSE"
        exp = int(c.get("expires") or 0)
        lines.append(f"{dom}\t{inc}\t{c.get('path','/')}\t{secure}\t{exp}\t{c.get('name')}\t{c.get('value')}")
    COOKIE_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(lines) - 1

def douyin_unavailable_reason(vid):
    """返回失效原因；可正常获取返回 None。"""
    detail, err = aweme_detail(vid)
    return f"作品不可获取：{err}" if err else None


def download_audio(ctx, page, r):
    vid = r["id"]; url = r["url"]
    out = AUDIO_DIR / f"{vid}.mp3"
    if out.exists() and out.stat().st_size > 1000:
        return {"status": "exists", "path": out}
    try:
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
    except Exception:
        pass
    cmd = [str(YDL), "--cookies", str(COOKIE_FILE),
           "-f", "bestaudio/best", "-x", "--audio-format", "mp3",
           "-o", str(AUDIO_DIR / f"{vid}.%(ext)s"), url]
    try:
        rp = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    if out.exists() and out.stat().st_size > 1000:
        return {"status": "ok", "path": out, "mb": round(out.stat().st_size/1024/1024, 1)}
    reason = douyin_unavailable_reason(vid)
    if reason:
        return {"status": "fail", "err": reason}
    return {"status": "fail", "err": (rp.stderr or rp.stdout or "")[-200:]}

def transcribe(model, mp3, vid):
    from faster_whisper import WhisperModel
    segs, info = model.transcribe(str(mp3), language="zh", vad_filter=True)
    chunks = []
    for s in segs:
        chunks.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()})
    full = "\n".join(c["text"] for c in chunks if c["text"])
    rec = {"id": vid, "duration": round(info.duration, 2) if info and info.duration else None,
           "full_text": full, "segments": chunks,
           "done_at": datetime.datetime.now().isoformat(timespec="seconds")}
    out = TRANS_DIR / f"{vid}.json"
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    return rec

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--ids", default="")
    ap.add_argument("--model", default="small")
    ap.add_argument("--max-minutes", type=float, default=40,
                    help="超过该时长(分钟)的超长视频直接跳过；0 表示不限制")
    ap.add_argument("--retry-dead", action="store_true",
                    help="重新尝试之前标记为失效的作品")
    args = ap.parse_args()

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    TRANS_DIR.mkdir(parents=True, exist_ok=True)

    rows = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else []
    if args.ids:
        wanted = [x.strip() for x in args.ids.split(",") if x.strip()]
        rows = [r for r in rows if r["id"] in wanted]
    if args.limit:
        rows = rows[:args.limit]
    if not rows:
        log("没有找到要处理的视频（检查 work/data/cleaned_tree.json）")
        return 1

    log(f"本次待处理 {len(rows)} 条 | 模型 {args.model}")

    # 连接 Chrome 导出 cookie
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        ctx = browser.contexts[0]
        n = write_cookies(ctx)
        log(f"已导出登录凭证 {n} 条")
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        # 加载/首次下载模型
        log("加载语音模型（优先用本地目录，缺失才会下载，国内会走镜像）…")
        import os as _os
        _os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
        from faster_whisper import WhisperModel
        local_model = PIPE_DIR / "models" / args.model
        if not local_model.is_dir():
            local_model = PIPE_DIR / "models" / f"faster-whisper-{args.model}"
        model_src = str(local_model) if local_model.is_dir() else args.model
        model = WhisperModel(model_src, device="cpu", compute_type="int8")

        total = len(rows)
        t0 = time.time()
        done = 0
        skipped_dead = skipped_long = newly_dead = 0
        state = load_state()
        for i, r in enumerate(rows, 1):
            vid = r["id"]
            out_json = TRANS_DIR / f"{vid}.json"
            if out_json.exists():
                done += 1
                continue

            # 已知失效 / 已知超长：直接跳过，不再浪费时间
            if vid in state["dead"] and not args.retry_dead:
                skipped_dead += 1
                continue
            if vid in state["too_long"]:
                skipped_long += 1
                continue

            # 预检查：一次接口调用同时拿到「是否失效」和「时长」
            if not (AUDIO_DIR / f"{vid}.mp3").exists():
                detail, err = aweme_detail(vid)
                if err:
                    state["dead"][vid] = {"reason": err, "title": r.get("title", "")[:60],
                                          "at": datetime.datetime.now().isoformat(timespec="seconds")}
                    save_state(state)
                    newly_dead += 1
                    log(f"[{i}/{total}] ✗ {vid} 作品已失效（将从结果中剔除）：{err}")
                    continue
                mins = video_minutes(detail) if detail else None
                if args.max_minutes and mins and mins > args.max_minutes:
                    state["too_long"][vid] = {"minutes": mins, "title": r.get("title", "")[:60],
                                              "at": datetime.datetime.now().isoformat(timespec="seconds")}
                    save_state(state)
                    skipped_long += 1
                    log(f"[{i}/{total}] ⏭ {vid} 超长视频 {mins} 分钟 > {args.max_minutes} 分钟，跳过")
                    continue
            # 1) 下载音频（若已下载则直接用）
            d = download_audio(ctx, page, r)
            mp3 = AUDIO_DIR / f"{vid}.mp3"
            if d.get("status") in ("ok", "exists") and mp3.exists():
                pass
            else:
                err = d.get("err", "")
                if "作品不可获取" in str(err):
                    state["dead"][vid] = {"reason": str(err), "title": r.get("title", "")[:60],
                                          "at": datetime.datetime.now().isoformat(timespec="seconds")}
                    save_state(state)
                    newly_dead += 1
                log(f"[{i}/{total}] {vid} 音频下载失败：{d.get('status')} {err}")
                continue
            # 2) 转写
            try:
                tr = transcribe(model, mp3, vid)
                log(f"[{i}/{total}] ✓ {vid} 转写完成：{len(tr['full_text'])}字")
                done += 1
            except Exception as e:
                log(f"[{i}/{total}] ✗ {vid} 转写失败：{e}")
            # 节流打印进度
            if i % 20 == 0 or i == total:
                el = time.time() - t0
                log(f"  进度 {i}/{total}，已转 {done}，用时 {el/60:.0f} 分钟")

        save_state(state)
        log(f"流程结束。完成 {done} 条 | 跳过失效 {skipped_dead + newly_dead} 条 "
            f"| 跳过超长 {skipped_long} 条")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("用户停止，进度已保存，再次运行即可续跑")
    except Exception as e:
        import traceback; traceback.print_exc()
        sys.exit(1)
