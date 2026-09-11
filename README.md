<div align="center">

# 🧭 抖音收藏知识库

**把抖音收藏夹变成可全文检索的个人知识库**

自动抓取收藏 → 下载音频 → AI 语音转文字 → 按「需求」分类 → 生成可搜索的网页

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-macOS-000000?logo=apple&logoColor=white)](https://www.apple.com/macos/)
[![Whisper](https://img.shields.io/badge/ASR-faster--whisper-FF6F00)](https://github.com/SYSTRAN/faster-whisper)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![离线转写](https://img.shields.io/badge/语音转写-100%25本地-success)](#-隐私说明)

[快速开始](#-快速开始) · [技术教程](docs/技术教程.md) · [小白教程](docs/小白教程.md) · [常见问题](#-常见问题)

</div>

---

## 💡 为什么做这个

刷到有用的视频就收藏，攒了几百条。可真遇到问题时：

- **搜不到** — 抖音只能搜标题，而标题往往是「9021 Codex太强了…」，真正的干货全在语音里
- **想不起** — 压根记不得自己收藏过相关内容
- **分类无效** — 按话题分（AI / 生活 / 教育），400 条全挤在「AI」里，等于没分

这个工具把每条视频的**语音转成文字**，再按「**我将来遇到什么问题会来翻它**」重新组织。

> 想找「装修要注意什么」？搜一下，几百条里立刻定位，还能直接看到人家具体说了什么。

---

## ✨ 效果

跑完会在 `outputs/` 得到 4 个文件：

| 产物 | 说明 |
|---|---|
| 📄 **收藏文案.html** | 全文可搜索，完整文案 + 时间轴，支持一键复制 |
| 🧭 **收藏脑图.html** | 三级需求分类导航，回答「我这个问题该翻哪一类」 |
| 📊 **收藏文案.csv** | Excel 打开，含分类 / 术语 / 形态字段 |
| 📝 **收藏文案.txt** | 纯文本，方便整份喂给 AI 分析 |

**真实运行数据**（作者本人 701 条收藏）：

```
已转写 664 条  ·  无人声 30 条  ·  超长跳过 2 条  ·  已失效 5 条
耗时约 18 小时（M 系列芯片，全程本地）
```

### 三个检索维度

不止是分类，而是三个正交维度组合定位：

```
需求分类（找什么领域）  ×  内容形态（要什么类型）  ×  术语（精确定位）

AI 编程与智能体          保姆级教程                  Claude Code
  └ 能力扩展             实战案例                    MCP
     └ Skills 技能       避坑经验                    RAG
                        工具推荐 / 原理讲解 / 资源合集
```

想快速上手 Codex → 筛「保姆级教程」；想避雷 → 筛「避坑经验」。

---

## 🚀 快速开始

### 环境要求

- macOS（Windows / Linux 需自行改写 `.command` 启动脚本）
- Python 3.9+ · ffmpeg · Google Chrome
- 磁盘约 2GB（音频 + 语音模型）

### 三步走

```bash
git clone https://github.com/jerryzhou998/douyin-fav-kb.git
cd douyin-fav-kb
```

然后依次**双击**：

| 步骤 | 文件 | 作用 | 耗时 |
|:--:|---|---|---|
| 0️⃣ | `0-一键安装.command` | 装依赖 + 下载语音模型 | 首次 5-10 分钟 |
| 1️⃣ | `1-抓取收藏.command` | 抓取收藏 + 清洗分类 | 几分钟 |
| 2️⃣ | `2-转写出稿.command` | 后台转写 + 生成成品 | 700 条约 18 小时 |

> [!NOTE]
> **第 1 步需要你手动介入**：脚本会打开专用 Chrome，你登录抖音并进入「我的收藏 → 视频」，回终端按回车。
> 抖音登录有风控，这一步无法自动化。这个 Chrome 用独立配置，不影响你日常浏览器。

> [!TIP]
> **第 2 步启动后转入后台**，可以直接关掉窗口。想看进度：`tail -f step2.log`

### 日常增量更新

以后再跑，只处理新增的：

- 抓取时**连续遇到 40 条已抓过的就自动停**
- 转写时已完成的直接跳过
- 新收藏 20 条，约 20 分钟更新完

---

## 🏗 工作原理

```
                    抖音收藏页
                        │  Playwright 连接真实 Chrome
                        │  监听 XHR 响应 + DOM 兜底双通道
                        ▼
              favorites.jsonl（边抓边存，断点续抓）
                        │
                        ▼  build_km3.py
                cleaned_tree.json（清洗去重）
                        │
                        ▼  transcribe_pipeline.py
        ┌───────────────┴───────────────┐
        │ 预检查：调 detail 接口拿时长    │
        │  ├ 已失效  → 记入 state 跳过   │
        │  └ 超 40 分 → 跳过             │
        │ yt-dlp 下载音频（复用 Cookie） │
        │ faster-whisper 本地转写        │
        └───────────────┬───────────────┘
                        ▼
              transcripts/*.json（一条一文件）
                        │
                        ▼  enrich_classify.py + taxonomy.py
        需求三级分类 + 可检索术语 + 内容形态
                        │
                        ▼  build_transcript_view.py / build_mindmap.py
              outputs/  收藏文案.html · 收藏脑图.html · .csv · .txt
```

### 技术选型

| 环节 | 方案 | 理由 |
|---|---|---|
| 抓取 | Playwright + 真实 Chrome | 抖音风控强，签名逆向成本高 |
| 下载 | yt-dlp | CDN 地址有时效签名，已处理好 |
| 转写 | faster-whisper (small/int8) | 本地跑、免费、中文够用 |
| 分类 | 规则 + 权重打分 | 可解释、可调、零成本 |
| 输出 | 单文件 HTML | 双击即用，无需服务器 |

> **为什么分类不用 LLM？** 700 条调 API 要钱，且同样输入可能给出不同结果。
> 规则引擎虽然要手写词表，但完全可控——归错了改一行重跑，几秒钟。

---

## 📁 项目结构

```
douyin-fav-kb/
├── 0-一键安装.command          环境安装
├── 1-抓取收藏.command          第一步入口
├── 2-转写出稿.command          第二步入口（后台运行）
├── grab.py                     抓取收藏，增量 + 断点续抓
├── build_km3.py                清洗去重
├── transcribe_pipeline.py      下载音频 + 语音转文字
├── pipeline_common.py          抖音接口、失效判定、状态库
├── taxonomy.py                 ⭐ 分类体系与术语词典
├── enrich_classify.py          用文案重新分类、抽术语、判形态
├── build_transcript_view.py    生成文案库
├── build_mindmap.py            生成需求脑图
└── docs/
    ├── 技术教程.md             实现原理 + 踩坑记录
    └── 小白教程.md             让 Codex 帮你搭
```

**最值得定制的是 [`taxonomy.py`](taxonomy.py)** — 分类规则就是一张表，按自己的需求改：

```python
TAXONOMY = [
    ("AI 编程与智能体", "能力扩展", "Skills 技能",
     [("skills", W_STRONG), ("agentsskills", W_STRONG), ("技能包", W_MED)]),
    # (一级, 二级, 三级, [(关键词, 权重)])
]
```

改完跑一次 `enrich_classify.py`，几秒重算，**不用重新转写**。

---

## 📚 两份教程

<table>
<tr>
<td width="50%" valign="top">

### 👨‍💻 [技术教程](docs/技术教程.md)

面向技术人员，讲**为什么这么设计**和踩过的坑：

- 抖音风控怎么绕：监听 XHR 而非逆向签名
- 内嵌滚动容器的定位技巧
- `Fresh cookies needed` 报错的真实原因排查
- HuggingFace 镜像下载失败的根因与绕法
- 分类权重打分的设计（标题 ×10、命中封顶）
- 中英文混合匹配为何要分流处理

</td>
<td width="50%" valign="top">

### 🙋 [小白教程](docs/小白教程.md)

不懂编程？**让 Codex 帮你搭**：

- 附一段可直接复制的完整提示词
- 已把 5 个坑写进提示词，AI 一次做对
- 常见报错对照表
- 耗时预期与操作要点
- 改需求的示例话术

> 核心心法：**把报错原样贴给 Codex，它会自己修**

</td>
</tr>
</table>

---

## ❓ 常见问题

<details>
<summary><b>抓取只拿到几条就停了？</b></summary>

抖音收藏页是**内嵌滚动容器**，不是整个窗口在滚。脚本会自动找真正滚动的元素，但如果抖音改版可能失效。
确认你已经进入「我的收藏 → **视频**」标签页，而不是收藏夹首页。

</details>

<details>
<summary><b>报错 Fresh cookies (not necessarily logged in) are needed</b></summary>

**不是 Cookie 问题**。这是 yt-dlp 拿不到作品详情时的通用兜底提示，真实原因通常是**作品已被作者删除或设为私密**。

本项目已处理：会额外调抖音 `aweme/detail` 接口确认真实原因，并把失效作品记入 `data/state.json`，之后不再重试。

</details>

<details>
<summary><b>语音模型下载失败</b></summary>

新版 `huggingface_hub` 走 Xet 存储协议，国内镜像的重定向链上丢了 `X-Repo-Commit` 头，导致自动下载失败。

`0-一键安装.command` 已绕开该问题：直接用 `curl` 从 hf-mirror 下到 `models/` 目录，再按路径加载。支持断点续传。

</details>

<details>
<summary><b>关掉终端窗口后任务停了</b></summary>

第 2 步用了 `nohup` + `disown` 真正脱离终端，关窗口不影响。
如果你自己改过脚本，注意只用 `&` 是不够的。

查看进度：`tail -f step2.log`

</details>

<details>
<summary><b>转写太慢 / 想更准</b></summary>

改模型大小即可，在 `2-转写出稿.command` 里调 `--model` 参数：

| 模型 | 速度 | 精度 | 体积 |
|---|---|---|---|
| `tiny` | 最快 | 一般 | 75MB |
| `small` | 中等（默认） | 够用 | 460MB |
| `medium` | 慢 | 好 | 1.5GB |

</details>

<details>
<summary><b>超长视频怎么处理</b></summary>

默认跳过 40 分钟以上的（一条 3 小时 48 分的视频要转 1 小时以上）。
改阈值：`2-转写出稿.command` 里的 `MAXMIN=40`。设成 `0` 表示不限制。

</details>

---

## 🔒 隐私说明

- **语音转写 100% 在本地完成**，不调用任何云端 API，视频内容不上传
- Cookie 仅保存在本地 `cookies.txt`，已加入 `.gitignore`
- 抓取的数据、音频、转写结果全部留在你自己电脑上

> ⚠️ 仅供整理**自己的**收藏内容使用，请勿用于批量抓取他人内容。

---

## 🗺 Roadmap

- [ ] LLM 兜底分类（规则未命中的 8% 交给 LLM）
- [ ] 语义搜索（embedding 向量检索，支持自然语言查询）
- [ ] 同步到飞书多维表格 / Notion
- [ ] 并发转写（目前串行）
- [ ] Windows / Linux 支持

---

## 📄 License

[MIT](LICENSE) — 随意使用和修改。

---

<div align="center">
<sub>如果这个项目对你有用，欢迎 ⭐ Star</sub>
</div>
