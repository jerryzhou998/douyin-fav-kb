#!/bin/zsh
# 首次使用请先双击本文件，安装运行环境。
cd "$(dirname "$0")"
set -e

echo "════════════════════════════════════════════════════"
echo "  抖音收藏知识库 · 环境安装"
echo "════════════════════════════════════════════════════"
echo ""

# 1) Python
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ 没找到 python3。请先安装 Xcode 命令行工具："
  echo "   xcode-select --install"
  read -r "?按回车关闭... "; exit 1
fi
echo "✓ Python: $(python3 -V)"

# 2) ffmpeg（音频转码必需）
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "⚠️  没找到 ffmpeg，正在尝试用 Homebrew 安装…"
  if command -v brew >/dev/null 2>&1; then
    brew install ffmpeg
  else
    echo "❌ 也没找到 Homebrew。请先安装 Homebrew："
    echo '   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    echo "   然后再运行本脚本。"
    read -r "?按回车关闭... "; exit 1
  fi
fi
echo "✓ ffmpeg: $(ffmpeg -version 2>/dev/null | head -1 | cut -d' ' -f3)"

# 3) 虚拟环境 + 依赖
if [ ! -x ".venv/bin/python" ]; then
  echo ""
  echo "→ 创建虚拟环境 .venv …"
  python3 -m venv .venv
fi
echo "→ 安装依赖（首次约 3-5 分钟）…"
./.venv/bin/pip install --upgrade pip -q
./.venv/bin/pip install -r requirements.txt -q
echo "✓ 依赖安装完成"

# 4) Playwright 浏览器驱动
echo "→ 安装 Playwright 驱动…"
./.venv/bin/python -m playwright install chromium 2>/dev/null || true

# 5) 下载语音模型（走国内镜像，避免连不上 HuggingFace）
MODEL_DIR="models/faster-whisper-small"
if [ ! -f "$MODEL_DIR/model.bin" ]; then
  echo ""
  echo "→ 下载语音识别模型（约 460MB，走国内镜像）…"
  mkdir -p "$MODEL_DIR"
  BASE="https://hf-mirror.com/Systran/faster-whisper-small/resolve/main"
  for f in config.json tokenizer.json vocabulary.txt; do
    curl -sL --retry 3 -o "$MODEL_DIR/$f" "$BASE/$f"
  done
  curl -L --retry 3 -C - -o "$MODEL_DIR/model.bin" "$BASE/model.bin"
fi
echo "✓ 语音模型就绪"

echo ""
echo "════════════════════════════════════════════════════"
echo "  安装完成！接下来："
echo "    1) 双击【1-抓取收藏.command】"
echo "    2) 双击【2-转写出稿.command】"
echo "════════════════════════════════════════════════════"
read -r "?按回车关闭... "
