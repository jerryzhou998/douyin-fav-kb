#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""转写完成后：按「需求导向」重新分类 + 抽取可检索术语 + 判定内容形态。

分类哲学：不按话题领域分，而按「我将来遇到什么问题会来翻它」分。
输出 data/enriched.json，字段：
  path      三级分类（需求 → 场景 → 具体方案）
  terms     可检索术语（Claude Code / MCP / RAG / 装修避坑…）
  form      内容形态（保姆级教程 / 实战案例 / 工具推荐 / 原理讲解 / 避坑经验 / 资源合集）
"""
import json, argparse, sys
from collections import Counter
from pathlib import Path

PIPE = Path(__file__).resolve().parent
sys.path.insert(0, str(PIPE))
import taxonomy
from pipeline_common import load_state

DATA = PIPE / "data"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=str(DATA / "cleaned_tree.json"))
    ap.add_argument("--trans", default=str(DATA / "transcripts"))
    ap.add_argument("--out", default=str(DATA / "enriched.json"))
    args = ap.parse_args()

    rows = json.loads(Path(args.inp).read_text(encoding="utf-8"))
    tdir = Path(args.trans)
    state = load_state()
    dead, too_long = state.get("dead", {}), state.get("too_long", {})

    out, stats = [], Counter()
    for r in rows:
        vid = r["id"]
        if vid in dead:
            stats["剔除失效"] += 1
            continue

        tp = tdir / f"{vid}.json"
        tr = json.loads(tp.read_text(encoding="utf-8")) if tp.exists() else None
        full = (tr or {}).get("full_text", "").strip()
        title, tags = r.get("title", ""), r.get("tags", "")

        path, score, src = taxonomy.classify(title, tags, full)
        terms = taxonomy.extract_terms(title, tags, full)
        form = taxonomy.detect_form(title, tags, full)

        stats[f"依据:{src}"] += 1
        stats[f"形态:{form}"] += 1

        rec = dict(r)
        rec["path"] = path
        rec["terms"] = terms
        rec["keywords"] = terms          # 兼容旧字段
        rec["form"] = form
        rec["score"] = score
        rec["classify_by"] = src
        rec["transcript"] = full
        rec["duration"] = (tr or {}).get("duration")
        rec["chars"] = len(full)
        if vid in too_long:
            rec["status"] = "too_long"
            rec["note"] = f"超长视频（{too_long[vid].get('minutes')} 分钟），已跳过转写"
        elif not tp.exists():
            rec["status"] = "pending"
        elif not full:
            rec["status"] = "empty"
        else:
            rec["status"] = "ok"
        out.append(rec)

    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[需求导向分类] 输出 {len(out)} 条 → {args.out}")
    c1 = Counter(r["path"][0] for r in out)
    print("\n按『我要解决什么问题』分：")
    for k, v in c1.most_common():
        print(f"  {v:4d}  {k}")
    print("\n内容形态：")
    for k, v in stats.most_common():
        if k.startswith("形态:"):
            print(f"  {v:4d}  {k[3:]}")
    nt = Counter(t for r in out for t in r["terms"])
    print("\n高频术语 Top20：")
    print("  " + "、".join(f"{k}({v})" for k, v in nt.most_common(20)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
