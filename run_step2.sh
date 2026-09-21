#!/bin/zsh
# 第二步的实际执行体（由 2-转写出稿.command 派生到后台运行）
cd "$(dirname "$0")"
export PYTHONUTF8=1
export PYTHONPATH="$(pwd)"
PY="$(pwd)/.venv/bin/python"
MAXMIN="${MAXMIN:-40}"
if [ ! -x "$PY" ]; then
  echo "[$(date '+%F %T')] ❌ 缺少运行环境，请先双击【0-一键安装.command】。已中止。"
  exit 1
fi


echo "[$(date '+%F %T')] ===== 第 2 步开始（后台） ====="

echo "[$(date '+%F %T')] --- 2.1 下载音频 + 语音转文字 ---"
RC1=0
"$PY" transcribe_pipeline.py --max-minutes "$MAXMIN" || RC1=$?

echo "[$(date '+%F %T')] --- 2.2 用文案重新分类 + 抽关键词 ---"
"$PY" enrich_classify.py

echo "[$(date '+%F %T')] --- 2.3 生成文案库（HTML/CSV/TXT） ---"
"$PY" build_transcript_view.py

echo "[$(date '+%F %T')] --- 2.4 生成需求脑图 ---"
"$PY" build_mindmap.py

echo "[$(date '+%F %T')] --- 2.5 同步到 Obsidian ---"
"$PY" export_obsidian.py

if [ "$RC1" -ne 0 ]; then
  echo "[$(date '+%F %T')] ===== 完成，但转写步骤失败（见上方日志），新视频尚未转写 ====="
else
  echo "[$(date '+%F %T')] ===== 全部完成 ====="
fi
