#!/bin/zsh
# 第一步：抓取抖音收藏（增量）+ 清洗分类 + 生成脑图
cd "$(dirname "$0")"
export PYTHONUTF8=1
export PYTHONPATH="$(pwd)"
export PYTHONPYCACHEPREFIX="$(pwd)/.pycache"
PY="$(pwd)/.venv/bin/python"
# 环境自检：缺 .venv 时给出明确指引，避免 zsh 直接报 127
if [ ! -x "$(pwd)/.venv/bin/python" ]; then
  echo ""
  echo "❌ 还没安装运行环境（缺少 .venv）。"
  echo "   请先双击本文件夹里的【0-一键安装.command】，"
  echo "   等它安装完成后，再运行本脚本。"
  echo ""
  read -k1 -r "?按任意键关闭... "
  exit 1
fi

PROFILE="$HOME/.codex-douyin-profile"

echo "════════════════════════════════════════════════════"
echo "  第 1 步：抓取抖音收藏（增量模式）"
echo "════════════════════════════════════════════════════"
echo "会打开专用 Chrome。请："
echo "  1) 确认已登录抖音"
echo "  2) 进入【我的收藏 → 视频】列表页"
echo "  3) 回到本窗口按回车"
echo ""
echo "增量说明：连续遇到 40 条以前抓过的旧视频就自动停止，"
echo "          所以只会抓新增的那些，很快。"
echo "════════════════════════════════════════════════════"
echo ""

"$PY" grab.py --profile "$PROFILE" --out "$(pwd)/data" --incremental
rc=$?
if [ $rc -ne 0 ]; then
  echo "抓取中断（代码 $rc），已抓内容已保存。"
  read -r "?按回车关闭... "
  exit $rc
fi

echo ""
echo "──────── 清洗、去重、分类 ────────"
"$PY" build_km3.py --in "$(pwd)/data/favorites.jsonl" \
  --out "" \
  --csv "$(pwd)/data/cleaned_tree.csv" \
  --json "$(pwd)/data/cleaned_tree.json"
"$PY" enrich_classify.py
echo "──────── 生成新版脑图与文案库 ────────"
"$PY" build_transcript_view.py
"$PY" build_mindmap.py
"$PY" export_obsidian.py

echo ""
echo "════════════════════════════════════════════════════"
echo "  第 1 步完成！"
echo "  脑图：outputs/收藏脑图.html"
echo ""
echo "  接下来双击【2-转写出稿.command】，它会在后台"
echo "  慢慢把新视频转成文字，你可以关掉窗口不用管。"
echo "════════════════════════════════════════════════════"
read -r "?按回车关闭... "
