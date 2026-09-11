#!/bin/zsh
# 双击或运行: ./start-douyin-chrome.command
# 作用：以“专用资料夹”启动一个 Chrome，供抓取工具远程连接（不影响你日常 Chrome）

PROFILE_DIR="$HOME/.codex-douyin-profile"
mkdir -p "$PROFILE_DIR"

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if [ ! -x "$CHROME" ]; then
  echo "未找到 Chrome，请确认安装后重试。"
  read -n1 -r -p "按任意键关闭..."
  exit 1
fi

echo "正在启动专用 Chrome 窗口，请在弹出的窗口里登录抖音，并进入【收藏】列表…"
echo "如果弹出新窗口，请在该窗口操作；关掉后自动结束。"
"$CHROME" \
  --remote-debugging-port=9222 \
  --user-data-dir="$PROFILE_DIR" \
  --no-first-run \
  --no-default-browser-check \
  "https://www.douyin.com" >/dev/null 2>&1

echo "Chrome 窗口已关闭。"
read -n1 -r -p "按任意键关闭本窗口..."
