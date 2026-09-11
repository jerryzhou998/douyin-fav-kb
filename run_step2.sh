#!/bin/zsh
# 第二步的实际执行体（由 2-转写出稿.command 派生到后台运行）
cd "$(dirname "$0")"
export PYTHONUTF8=1
export PYTHONPATH="$(pwd)"
PY="$(pwd)/.venv/bin/python"
MAXMIN="${MAXMIN:-40}"

echo "[$(date '+%F %T')] ===== 第 2 步开始（后台） ====="

echo "[$(date '+%F %T')] --- 2.1 下载音频 + 语音转文字 ---"
"$PY" transcribe_pipeline.py --max-minutes "$MAXMIN"

echo "[$(date '+%F %T')] --- 2.2 用文案重新分类 + 抽关键词 ---"
"$PY" enrich_classify.py

echo "[$(date '+%F %T')] --- 2.3 生成文案库（HTML/CSV/TXT） ---"
"$PY" build_transcript_view.py

echo "[$(date '+%F %T')] --- 2.4 生成需求脑图 ---"
"$PY" build_mindmap.py

echo "[$(date '+%F %T')] ===== 全部完成 ====="
