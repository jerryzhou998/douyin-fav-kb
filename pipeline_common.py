#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公共工具：抖音作品详情、失效判定、状态库（state.json）。"""
import json, urllib.request, urllib.parse, datetime
from pathlib import Path

PIPE_DIR = Path(__file__).resolve().parent
DATA_DIR = PIPE_DIR / "data"
COOKIE_FILE = PIPE_DIR / "cookies.txt"
STATE_FILE = DATA_DIR / "state.json"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")


def load_state():
    """状态库：记录失效作品、超长跳过的作品，避免重复劳动。"""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"dead": {}, "too_long": {}, "updated_at": None}


def save_state(st):
    st["updated_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


def _cookies():
    c = {}
    if COOKIE_FILE.exists():
        for line in COOKIE_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "\t" not in line:
                continue
            p = line.split("\t")
            if len(p) >= 7:
                c[p[-2]] = p[-1]
    return c


def aweme_detail(vid, timeout=20):
    """返回 (detail_dict 或 None, 失效原因 或 None)。"""
    try:
        qs = urllib.parse.urlencode({
            "aweme_id": vid, "aid": "6383", "version_code": "170400",
            "device_platform": "webapp", "browser_language": "zh",
            "browser_platform": "MacOS", "browser_name": "Chrome",
            "browser_version": "152.0.7977.83",
        })
        req = urllib.request.Request(
            "https://www.douyin.com/aweme/v1/web/aweme/detail/?" + qs,
            headers={"User-Agent": UA, "Referer": "https://www.douyin.com/",
                     "Cookie": "; ".join(f"{k}={v}" for k, v in _cookies().items())})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return None, None  # 网络问题，不判定为失效
    ad = data.get("aweme_detail")
    if ad:
        return ad, None
    fd = data.get("filter_detail") or {}
    msg = fd.get("detail_msg") or fd.get("notice") or "作品不可获取"
    return None, msg


def video_minutes(detail):
    """作品时长（分钟）；拿不到返回 None。"""
    try:
        ms = (detail.get("video") or {}).get("duration")
        if ms:
            return round(ms / 60000, 1)
    except Exception:
        pass
    return None
