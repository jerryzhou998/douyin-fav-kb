#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按「将来遇到需求时，怎么找到别人的解决方案」重新设计的分类体系。

与旧版的区别：
  旧：按话题领域分（AI / 生活 / 教育…），400 条挤在「AI 与智能」里，检索无用。
  新：按【我想解决什么问题】分，二级是具体场景，三级是工具/方法。
      另加两个检索维度：术语标签（工具名/技术名）、内容形态（教程/实战/避坑…）。
"""
import re

W_STRONG, W_MED, W_WEAK = 3, 2, 1

# ============ 分类体系：(一级, 二级, 三级, [(关键词, 权重)]) ============
TAXONOMY = [
    # ── 1. 让 AI 帮我写代码 / 干活 ──────────────────────────
    ("AI 编程与智能体", "编程 Agent", "Claude Code",
     [("claude code", W_STRONG), ("claudecode", W_STRONG), ("claude", W_MED), ("cc ", W_WEAK)]),
    ("AI 编程与智能体", "编程 Agent", "Codex",
     [("codex", W_STRONG)]),
    ("AI 编程与智能体", "编程 Agent", "OpenClaw / Clawbot",
     [("openclaw", W_STRONG), ("winclaw", W_STRONG), ("clawbot", W_STRONG), ("龙虾", W_MED)]),
    ("AI 编程与智能体", "编程 Agent", "Cursor 及其他 IDE",
     [("cursor", W_STRONG), ("windsurf", W_STRONG), ("trae", W_STRONG), ("copilot", W_STRONG),
      ("通义灵码", W_STRONG), ("文心快码", W_STRONG), ("ai编程", W_MED), ("ai写代码", W_MED)]),
    ("AI 编程与智能体", "能力扩展", "Skills 技能",
     [("skills", W_STRONG), ("agentsskills", W_STRONG), ("技能包", W_MED),
      ("技能", W_WEAK), ("skill", W_MED)]),
    ("AI 编程与智能体", "能力扩展", "MCP 工具接入",
     [("mcp", W_STRONG), ("function call", W_MED), ("工具调用", W_MED)]),
    ("AI 编程与智能体", "能力扩展", "子代理与多智能体",
     [("subagent", W_STRONG), ("子代理", W_STRONG), ("多智能体", W_STRONG), ("多agent", W_STRONG),
      ("swarm", W_MED)]),
    ("AI 编程与智能体", "提示词与上下文工程", "提示词技巧",
     [("提示词", W_STRONG), ("prompt", W_STRONG), ("咒语", W_MED), ("指令", W_WEAK)]),
    ("AI 编程与智能体", "提示词与上下文工程", "上下文与记忆",
     [("上下文", W_STRONG), ("context", W_STRONG), ("记忆", W_MED), ("token", W_MED),
      ("缓存", W_MED), ("压缩", W_WEAK)]),
    ("AI 编程与智能体", "Vibe Coding 实战", "从零做产品",
     [("vibecoding", W_STRONG), ("vibe coding", W_STRONG), ("独立开发", W_MED),
      ("我用ai做", W_MED), ("从零开发", W_MED), ("做了一个", W_WEAK), ("小游戏", W_WEAK)]),
    ("AI 编程与智能体", "自动化工作流", "n8n / Coze / Dify",
     [("n8n", W_STRONG), ("coze", W_STRONG), ("扣子", W_STRONG), ("dify", W_STRONG),
      ("langgraph", W_STRONG), ("langchain", W_STRONG)]),
    ("AI 编程与智能体", "自动化工作流", "流程自动化",
     [("工作流", W_STRONG), ("自动化", W_MED), ("rpa", W_STRONG), ("数字员工", W_STRONG),
      ("自动操控", W_MED), ("批量处理", W_WEAK)]),
    ("AI 编程与智能体", "智能体应用", "Agent 搭建",
     [("agent", W_MED), ("智能体", W_MED), ("manus", W_STRONG), ("genspark", W_STRONG),
      ("workbuddy", W_STRONG)]),

    # ── 2. 搞懂大模型原理 / 自己搭 ──────────────────────────
    ("大模型原理与自建", "模型原理", "架构与机制",
     [("注意力机制", W_STRONG), ("注意力", W_MED), ("transformer", W_STRONG),
      ("激活函数", W_STRONG), ("moe", W_STRONG), ("模型架构", W_STRONG), ("神经网络", W_MED),
      ("参数量", W_MED), ("推理模型", W_MED), ("蒸馏", W_MED)]),
    ("大模型原理与自建", "RAG 与知识库", "向量库与检索",
     [("rag", W_STRONG), ("向量数据库", W_STRONG), ("向量库", W_STRONG), ("向量", W_MED),
      ("知识库", W_STRONG), ("milvus", W_STRONG), ("embedding", W_STRONG), ("检索", W_MED),
      ("第二大脑", W_MED)]),
    ("大模型原理与自建", "微调与训练", "微调实操",
     [("微调", W_STRONG), ("lora", W_STRONG), ("sft", W_STRONG), ("训练自己的", W_STRONG),
      ("数据集", W_MED), ("强化学习", W_MED), ("大模型训练", W_STRONG)]),
    ("大模型原理与自建", "本地部署与 API", "部署与调用",
     [("本地部署", W_STRONG), ("ollama", W_STRONG), ("vllm", W_STRONG), ("私有化部署", W_STRONG),
      ("api", W_MED), ("免费调用", W_STRONG), ("openrouter", W_STRONG), ("量化", W_MED),
      ("显存", W_MED), ("本地运行", W_MED), ("断网", W_WEAK)]),
    ("大模型原理与自建", "模型产品与动态", "主流模型对比",
     [("deepseek", W_MED), ("qwen", W_MED), ("通义千问", W_MED), ("豆包", W_MED),
      ("gemini", W_MED), ("chatgpt", W_MED), ("openai", W_MED), ("kimi", W_MED),
      ("glm", W_MED), ("智谱", W_MED), ("llama", W_MED), ("grok", W_MED),
      ("大模型", W_WEAK), ("多模态", W_MED), ("视觉大模型", W_MED)]),

    ("大模型原理与自建", "行业动态与就业", "AI 趋势 / 职业影响",
     [("ai就业", W_STRONG), ("ai取代", W_STRONG), ("ai时代", W_STRONG),
      ("被ai取代", W_STRONG), ("ai岗位", W_STRONG), ("码农", W_MED),
      ("ai风口", W_STRONG), ("职业定位", W_STRONG), ("初体验", W_MED),
      ("发布", W_WEAK), ("最新模型", W_STRONG), ("omni", W_STRONG)]),
    ("大模型原理与自建", "算力与硬件选型", "GPU 与算力",
     [("gpu", W_STRONG), ("算力", W_STRONG), ("显卡", W_MED), ("4090", W_STRONG),
      ("5090", W_STRONG), ("a100", W_STRONG), ("选型", W_MED)]),
    ("大模型原理与自建", "文档解析与 OCR", "OCR / 文档处理",
     [("ocr", W_STRONG), ("mineru", W_STRONG), ("monkeyocr", W_STRONG),
      ("文档解析", W_STRONG), ("pdf解析", W_STRONG)]),

    # ── 3. 用 AI 做内容 ──────────────────────────────────
    ("AI 内容创作", "视频生成", "即梦 / 可灵 / Seedance",
     [("即梦", W_STRONG), ("可灵", W_STRONG), ("seedance", W_STRONG), ("sora", W_STRONG),
      ("veo", W_STRONG), ("ai视频", W_STRONG), ("视频生成", W_STRONG), ("分镜", W_MED),
      ("ai漫剧", W_STRONG), ("动态漫", W_STRONG)]),
    ("AI 内容创作", "图像设计", "AI 绘画与出图",
     [("midjourney", W_STRONG), ("stable diffusion", W_STRONG), ("nano banana", W_STRONG),
      ("flux", W_STRONG), ("ai绘画", W_STRONG), ("ai图片", W_STRONG), ("ai生图", W_STRONG),
      ("出图", W_MED), ("ai脸", W_MED), ("3d模型", W_MED)]),
    ("AI 内容创作", "数字人与口播", "数字人制作",
     [("数字人", W_STRONG), ("口播", W_STRONG), ("ai分身", W_STRONG), ("真人出镜", W_MED),
      ("虚拟主播", W_STRONG)]),
    ("AI 内容创作", "音频与配音", "语音克隆 / AI 音乐",
     [("语音克隆", W_STRONG), ("配音", W_STRONG), ("tts", W_STRONG), ("ai音乐", W_STRONG),
      ("音色", W_MED), ("语音合成", W_STRONG), ("音频", W_WEAK)]),
    ("AI 内容创作", "设计与建模", "CAD / 3D 建模",
     [("cad", W_STRONG), ("3d建模", W_STRONG), ("建模", W_MED), ("trellis", W_STRONG),
      ("blender", W_STRONG), ("室内设计", W_MED)]),
    ("AI 内容创作", "写作与自媒体", "AI 写作 / 爆款内容",
     [("ai写作", W_STRONG), ("ai小说", W_STRONG), ("网文", W_MED), ("爆款", W_MED),
      ("文案生成", W_STRONG), ("自媒体", W_MED), ("公众号", W_MED)]),

    # ── 4. 找工具 / 找资源 ────────────────────────────────
    ("工具与资源发现", "开源项目", "GitHub 项目推荐",
     [("开源项目", W_STRONG), ("github", W_MED), ("开源", W_MED), ("星标", W_STRONG),
      ("star", W_WEAK), ("开箱即用", W_MED)]),
    ("工具与资源发现", "实用网站", "宝藏网站",
     [("网站推荐", W_STRONG), ("宝藏网站", W_STRONG), ("网站分享", W_STRONG),
      ("在线工具", W_STRONG), ("免费资源", W_STRONG), ("资源站", W_STRONG)]),
    ("工具与资源发现", "效率软件", "软件与插件推荐",
     [("神器", W_MED), ("效率工具", W_STRONG), ("工具推荐", W_STRONG), ("插件", W_MED),
      ("软件推荐", W_STRONG), ("ai工具", W_MED), ("个工具", W_STRONG)]),

    # ── 5. 办公 / 文档 ───────────────────────────────────
    ("办公与文档", "PPT 与汇报", "PPT 制作",
     [("ppt", W_STRONG), ("述职", W_STRONG), ("工作汇报", W_STRONG), ("工作总结", W_MED),
      ("演示文稿", W_STRONG)]),
    ("办公与文档", "表格与数据", "Excel 与数据分析",
     [("excel", W_STRONG), ("表格", W_MED), ("函数公式", W_STRONG), ("数据分析", W_MED),
      ("可视化", W_MED), ("wps", W_STRONG)]),
    ("办公与文档", "文档与笔记", "笔记与知识管理",
     [("notion", W_STRONG), ("obsidian", W_STRONG), ("飞书", W_STRONG), ("语雀", W_STRONG),
      ("思维导图", W_STRONG), ("笔记软件", W_STRONG), ("word", W_MED), ("pdf", W_MED)]),

    # ── 6. 编程基础 / 技术栈 ──────────────────────────────
    ("编程与技术基础", "语言与框架", "编程语言",
     [("python", W_MED), ("java", W_MED), ("golang", W_MED), ("前端", W_MED),
      ("后端", W_MED), ("全栈", W_MED), ("react", W_MED), ("vue", W_MED),
      ("网页开发", W_MED), ("小程序", W_MED)]),
    ("编程与技术基础", "运维与环境", "Docker / Linux / Git",
     [("docker", W_STRONG), ("linux", W_STRONG), ("git ", W_MED), ("服务器", W_MED),
      ("命令行", W_MED), ("终端", W_WEAK), ("nginx", W_STRONG)]),
    ("编程与技术基础", "学习路线", "入门路线图",
     [("学习路线", W_STRONG), ("路线图", W_STRONG), ("roadmap", W_STRONG),
      ("从零学", W_MED), ("入门教程", W_MED), ("八股", W_STRONG), ("面试题", W_MED)]),

    # ── 7. 学习 / 教育 ───────────────────────────────────
    ("学习与教育", "英语学习", "英语方法",
     [("英语", W_STRONG), ("单词", W_MED), ("语法", W_MED), ("口语", W_MED),
      ("新概念", W_STRONG), ("四六级", W_STRONG)]),
    ("学习与教育", "中小学教辅", "学科学习",
     [("数学", W_MED), ("语文", W_MED), ("物理", W_MED), ("化学", W_MED),
      ("初中", W_MED), ("高中", W_MED), ("小学", W_MED), ("教材", W_MED),
      ("考研", W_STRONG), ("高考", W_STRONG), ("刷题", W_MED)]),
    ("学习与教育", "育儿与亲子", "家庭教育",
     [("育儿", W_STRONG), ("亲子", W_STRONG), ("家庭教育", W_STRONG), ("孩子", W_MED),
      ("宝宝", W_MED), ("启蒙", W_MED), ("专注力", W_MED), ("兴趣班", W_STRONG)]),
    ("学习与教育", "知识科普", "通识与思维",
     [("涨知识", W_STRONG), ("科普", W_MED), ("冷知识", W_STRONG), ("历史", W_MED),
      ("诗词", W_MED), ("心理学", W_MED), ("认知", W_WEAK), ("思维模型", W_STRONG)]),

    # ── 8. 赚钱 / 商业 ───────────────────────────────────
    ("赚钱与商业", "副业变现", "个人副业",
     [("副业", W_STRONG), ("变现", W_STRONG), ("月入", W_STRONG), ("接单", W_STRONG),
      ("兼职", W_STRONG), ("超级个体", W_STRONG), ("ai收入", W_STRONG)]),
    ("赚钱与商业", "电商与跨境", "电商运营",
     [("跨境电商", W_STRONG), ("亚马逊", W_STRONG), ("amazon", W_STRONG), ("淘宝", W_MED),
      ("拼多多", W_MED), ("电商", W_MED), ("选品", W_STRONG), ("独立站", W_STRONG),
      ("tiktok", W_MED), ("shopify", W_STRONG)]),
    ("赚钱与商业", "营销与获客", "SEO / GEO / AI 搜索",
     [("geo", W_STRONG), ("aeo", W_STRONG), ("seo", W_STRONG), ("ai搜索", W_STRONG),
      ("被ai推荐", W_STRONG), ("搜索排名", W_STRONG)]),
    ("赚钱与商业", "营销与获客", "流量与转化",
     [("营销", W_STRONG), ("获客", W_STRONG), ("私域", W_STRONG), ("引流", W_STRONG),
      ("转化率", W_STRONG), ("投放", W_MED), ("客户", W_WEAK), ("询盘", W_STRONG)]),
    ("赚钱与商业", "短视频运营", "账号与流量玩法",
     [("短视频运营", W_STRONG), ("个人ip", W_STRONG), ("涨粉", W_STRONG),
      ("上热门", W_STRONG), ("流量密码", W_STRONG), ("短视频", W_MED),
      ("账号", W_MED), ("播放量", W_STRONG), ("对标", W_MED)]),
    ("赚钱与商业", "小生意与实体", "开店 / 摆摊",
     [("摆摊", W_STRONG), ("开店", W_STRONG), ("小生意", W_STRONG), ("加盟", W_STRONG),
      ("便利店", W_STRONG), ("选址", W_STRONG), ("实体店", W_STRONG),
      ("挣钱项目", W_STRONG), ("创业项目", W_STRONG)]),
    ("赚钱与商业", "商业思维", "认知与方法论",
     [("商业思维", W_STRONG), ("第一性原理", W_STRONG), ("信息差", W_STRONG),
      ("赚钱思维", W_STRONG), ("创业", W_MED), ("商业模式", W_STRONG), ("老板", W_WEAK)]),

    # ── 9. 投资 / 理财 ───────────────────────────────────
    ("投资与理财", "股市", "A股与个股",
     [("a股", W_STRONG), ("股票", W_STRONG), ("大盘", W_STRONG), ("科创", W_MED),
      ("散户", W_STRONG), ("macd", W_STRONG), ("涨停", W_MED), ("券商", W_MED)]),
    ("投资与理财", "宏观经济", "政策与趋势",
     [("美联储", W_STRONG), ("降息", W_STRONG), ("通胀", W_STRONG), ("经济", W_MED),
      ("逆回购", W_STRONG), ("货币政策", W_STRONG), ("非农", W_STRONG), ("gdp", W_STRONG)]),
    ("投资与理财", "贵金属与外汇", "黄金投资",
     [("黄金", W_STRONG), ("白银", W_STRONG), ("美债", W_STRONG), ("汇率", W_STRONG)]),
    ("投资与理财", "房产", "买房与法拍",
     [("法拍", W_STRONG), ("买房", W_STRONG), ("房价", W_STRONG), ("楼市", W_STRONG),
      ("不良资产", W_STRONG)]),

    # ── 10. 居家 / 生活 ──────────────────────────────────
    ("居家与生活", "装修改造", "装修避坑",
     [("装修", W_STRONG), ("水电", W_MED), ("瓷砖", W_STRONG), ("卫生间", W_MED),
      ("阳台", W_MED), ("户型", W_STRONG), ("家装", W_STRONG), ("断桥铝", W_STRONG),
      ("收纳", W_MED)]),
    ("居家与生活", "家电与选购", "选购攻略",
     [("家电", W_STRONG), ("空调", W_MED), ("冰箱", W_MED), ("洗衣机", W_MED),
      ("热水器", W_MED), ("小厨宝", W_STRONG), ("选购", W_MED), ("平替", W_MED)]),
    ("居家与生活", "生活技巧", "省钱与妙招",
     [("省钱", W_STRONG), ("小妙招", W_STRONG), ("生活小技巧", W_STRONG),
      ("实用小技巧", W_STRONG), ("避坑", W_MED), ("机票", W_MED), ("网购", W_MED)]),
    ("居家与生活", "汽车与出行", "用车知识",
     [("汽车", W_STRONG), ("用车", W_STRONG), ("驾驶", W_MED), ("轮胎", W_STRONG),
      ("燃油车", W_STRONG), ("新能源车", W_STRONG), ("车险", W_STRONG)]),

    # ── 11. 健康 / 身体 ──────────────────────────────────
    ("健康与医疗", "医学科普", "疾病与用药",
     [("医学科普", W_STRONG), ("医生", W_MED), ("症状", W_MED), ("药膏", W_MED),
      ("皮肤", W_MED), ("炎症", W_MED), ("治疗", W_MED), ("血糖", W_STRONG),
      ("血压", W_STRONG), ("颈椎", W_STRONG)]),
    ("健康与医疗", "中医养生", "中医调理",
     [("中医", W_STRONG), ("经方", W_STRONG), ("艾灸", W_STRONG), ("湿气", W_STRONG),
      ("养生", W_STRONG), ("穴位", W_STRONG)]),
    ("健康与医疗", "健身塑形", "锻炼方法",
     [("健身", W_STRONG), ("减肥", W_STRONG), ("塑形", W_STRONG), ("腹肌", W_STRONG),
      ("拉伸", W_STRONG), ("增肌", W_STRONG), ("居家锻炼", W_STRONG)]),

    # ── 12. 美食 ────────────────────────────────────────
    ("美食与烹饪", "家常菜", "做菜教程",
     [("做法", W_MED), ("食谱", W_STRONG), ("家常菜", W_STRONG), ("美食教程", W_STRONG),
      ("烹饪", W_STRONG), ("年夜饭", W_STRONG), ("硬菜", W_STRONG), ("烘焙", W_STRONG),
      ("腌制", W_MED), ("红烧", W_MED)]),
    ("美食与烹饪", "探店与特产", "美食推荐",
     [("探店", W_STRONG), ("必吃", W_STRONG), ("小吃", W_MED), ("特色美食", W_STRONG),
      ("地方美食", W_STRONG), ("农家", W_MED)]),

    # ── 13. 旅行 / 摄影 ──────────────────────────────────
    ("旅行与摄影", "旅行攻略", "目的地与行程",
     [("旅游", W_STRONG), ("旅行", W_STRONG), ("攻略", W_MED), ("徒步", W_STRONG),
      ("露营", W_STRONG), ("自驾", W_STRONG), ("景点", W_STRONG), ("小城", W_MED)]),
    ("旅行与摄影", "摄影技巧", "拍摄与构图",
     [("摄影", W_STRONG), ("构图", W_STRONG), ("拍照", W_STRONG), ("镜头", W_MED),
      ("人像", W_MED), ("机位", W_STRONG)]),
    ("旅行与摄影", "视频剪辑", "剪辑与调色",
     [("剪辑", W_STRONG), ("剪映", W_STRONG), ("调色", W_STRONG), ("运镜", W_STRONG),
      ("pr教程", W_STRONG), ("特效", W_MED), ("卡点", W_STRONG), ("转场", W_STRONG)]),

    # ── 14. 兴趣与休闲（非需求型，但也该归位） ──────────────
    ("兴趣与休闲", "影视与小说", "剧集 / 网文推荐",
     [("小说", W_STRONG), ("推文", W_STRONG), ("书荒", W_STRONG), ("国漫", W_STRONG),
      ("动漫", W_STRONG), ("电影", W_MED), ("剧", W_WEAK), ("追剧", W_STRONG),
      ("后续", W_WEAK), ("虐恋", W_STRONG)]),
    ("兴趣与休闲", "游戏", "游戏攻略",
     [("游戏", W_MED), ("打野", W_STRONG), ("段位", W_STRONG), ("王者", W_STRONG),
      ("使命召唤", W_STRONG), ("公测", W_STRONG), ("赛季", W_STRONG), ("装备", W_WEAK)]),
    ("兴趣与休闲", "音乐与情感", "歌曲 / 情感",
     [("好歌", W_STRONG), ("老歌", W_STRONG), ("音乐", W_MED), ("歌曲", W_STRONG),
      ("恋爱", W_STRONG), ("脱单", W_STRONG), ("追女生", W_STRONG), ("情感", W_MED),
      ("夫妻", W_MED), ("相处", W_WEAK)]),
    ("兴趣与休闲", "运动与手工", "体育 / DIY",
     [("足球", W_STRONG), ("篮球", W_STRONG), ("乒乓球", W_STRONG), ("羽毛球", W_STRONG),
      ("手工diy", W_STRONG), ("手工", W_MED), ("书法", W_STRONG), ("手写", W_STRONG),
      ("行楷", W_STRONG), ("运球", W_STRONG)]),
    ("兴趣与休闲", "棋牌与益智", "棋牌技巧",
     [("掼蛋", W_STRONG), ("麻将", W_STRONG), ("斗地主", W_STRONG), ("象棋", W_STRONG),
      ("围棋", W_STRONG), ("记牌", W_STRONG), ("扑克", W_STRONG)]),
    ("兴趣与休闲", "国学与文化", "传统文化",
     [("国学", W_STRONG), ("传统文化", W_STRONG), ("儒家", W_STRONG), ("道德经", W_STRONG),
      ("易经", W_STRONG), ("修炼", W_MED), ("非遗", W_STRONG), ("大漆", W_STRONG)]),

    # ── 15. 机器人 / 硬件 ────────────────────────────────
    ("机器人与硬件", "具身智能", "人形与四足",
     [("人形机器人", W_STRONG), ("宇树", W_STRONG), ("unitree", W_STRONG),
      ("机器狗", W_STRONG), ("四足", W_STRONG), ("具身智能", W_STRONG), ("灵巧手", W_STRONG),
      ("机械臂", W_STRONG)]),
    ("机器人与硬件", "数码选购", "电脑手机选购",
     [("笔记本电脑", W_STRONG), ("笔记本", W_MED), ("手机", W_MED), ("平板", W_MED),
      ("上手实测", W_STRONG), ("入手", W_MED), ("配置", W_WEAK), ("性价比", W_MED)]),
    ("机器人与硬件", "智能硬件", "设备与装备",
     [("单片机", W_STRONG), ("树莓派", W_STRONG), ("arduino", W_STRONG),
      ("智能头盔", W_STRONG), ("3d打印", W_STRONG), ("无人机", W_STRONG),
      ("硬盘", W_MED), ("显卡", W_MED)]),
]

# ============ 术语词典：规范名 -> 别名（用于关键词标签） ============
TERMS = {
    "Claude Code": ["claude code", "claudecode"], "Claude": ["claude"],
    "Codex": ["codex"], "Cursor": ["cursor"], "Copilot": ["copilot"],
    "Windsurf": ["windsurf"], "Trae": ["trae"],
    "OpenClaw": ["openclaw"], "WinClaw": ["winclaw"], "Clawbot": ["clawbot"],
    "Skills": ["skills", "agentsskills"], "MCP": ["mcp"],
    "子代理": ["subagent", "子代理"], "多智能体": ["多智能体", "多agent"],
    "提示词工程": ["提示词", "prompt"], "上下文工程": ["上下文", "context engineering"],
    "Agent 记忆": ["agent记忆", "ai记忆", "记忆框架"],
    "Vibe Coding": ["vibecoding", "vibe coding"],
    "n8n": ["n8n"], "Coze": ["coze", "扣子"], "Dify": ["dify"],
    "LangChain": ["langchain"], "LangGraph": ["langgraph"],
    "工作流": ["工作流"], "RPA": ["rpa"], "数字员工": ["数字员工"],
    "Agent": ["agent", "智能体"], "Manus": ["manus"], "Genspark": ["genspark"],
    "RAG": ["rag"], "向量数据库": ["向量数据库", "向量库", "milvus"],
    "知识库": ["知识库"], "Embedding": ["embedding"],
    "微调": ["微调", "lora", "sft"], "模型训练": ["大模型训练", "训练自己的"],
    "本地部署": ["本地部署", "私有化部署", "ollama", "vllm"],
    "API 调用": ["api"], "注意力机制": ["注意力"], "Transformer": ["transformer"],
    "MoE": ["moe"], "蒸馏": ["蒸馏"], "多模态": ["多模态"],
    "DeepSeek": ["deepseek"], "Qwen": ["qwen", "通义千问"], "豆包": ["豆包"],
    "Gemini": ["gemini"], "GPT": ["gpt", "chatgpt"], "OpenAI": ["openai"],
    "Kimi": ["kimi"], "GLM": ["glm", "智谱"], "Llama": ["llama"], "Grok": ["grok"],
    "即梦": ["即梦"], "可灵": ["可灵"], "Seedance": ["seedance"], "Sora": ["sora"],
    "Midjourney": ["midjourney"], "Stable Diffusion": ["stable diffusion"],
    "Nano Banana": ["nano banana"], "Flux": ["flux"],
    "数字人": ["数字人"], "口播": ["口播"], "语音克隆": ["语音克隆"],
    "AI 音乐": ["ai音乐"], "AI 视频": ["ai视频", "视频生成"], "AI 绘画": ["ai绘画", "ai生图"],
    "开源项目": ["开源项目", "开源"], "GitHub": ["github"],
    "PPT": ["ppt"], "Excel": ["excel"], "Notion": ["notion"],
    "Obsidian": ["obsidian"], "飞书": ["飞书"], "思维导图": ["思维导图"],
    "Python": ["python"], "Docker": ["docker"], "Linux": ["linux"],
    "前端": ["前端"], "后端": ["后端"], "全栈": ["全栈"],
    "学习路线": ["学习路线", "路线图", "roadmap"],
    "英语": ["英语"], "育儿": ["育儿", "亲子"], "家庭教育": ["家庭教育"],
    "副业": ["副业"], "变现": ["变现"], "跨境电商": ["跨境电商"],
    "亚马逊": ["亚马逊", "amazon"], "私域": ["私域"], "营销": ["营销"],
    "商业思维": ["商业思维"], "第一性原理": ["第一性原理"],
    "A股": ["a股"], "美联储": ["美联储"], "黄金": ["黄金"], "法拍房": ["法拍"],
    "装修避坑": ["装修避坑"], "装修": ["装修"], "收纳": ["收纳"],
    "省钱": ["省钱"], "医学科普": ["医学科普"], "中医": ["中医"],
    "健身": ["健身"], "减肥": ["减肥"], "食谱": ["食谱", "家常菜"],
    "摄影": ["摄影"], "旅行": ["旅游", "旅行"],
    "OCR": ["ocr", "mineru", "monkeyocr"], "GPU 算力": ["gpu", "算力", "4090", "5090"],
    "短视频运营": ["短视频运营", "个人ip"], "AI 就业": ["ai就业", "ai取代"],
    "CAD/3D": ["cad", "3d建模"], "SEO/GEO": ["geo", "aeo", "seo"], "剪映": ["剪映"], "调色": ["调色"],
    "运镜": ["运镜"], "人形机器人": ["人形机器人"], "宇树": ["宇树", "unitree"], "机器狗": ["机器狗"],
    "具身智能": ["具身智能"], "3D 打印": ["3d打印"],
}

# ============ 内容形态：回答「这条是什么类型的资料」 ============
FORMS = [
    ("保姆级教程", [r"保姆级", r"手把手", r"喂饭", r"教程", r"实操", r"从零", r"零基础",
                r"详细步骤", r"一步步", r"怎么做", r"如何搭"]),
    ("实战案例", [r"实战", r"案例", r"演示", r"复刻", r"我用[^\s]{0,6}做", r"做了一个",
               r"全程记录", r"实测", r"挑战\d*天", r"第\d+天"]),
    ("工具推荐", [r"推荐", r"神器", r"好用", r"第\s*\d+\s*个工具", r"分享一个", r"安利",
               r"必备", r"宝藏"]),
    ("原理讲解", [r"原理", r"讲透", r"详解", r"什么是", r"区别", r"架构", r"为什么",
               r"底层", r"机制", r"深度解析"]),
    ("避坑经验", [r"避坑", r"坑", r"别买", r"别报", r"教训", r"后悔", r"注意",
               r"智商税", r"翻车"]),
    ("资源合集", [r"合集", r"大全", r"汇总", r"整理了", r"路线图", r"\d{2,}个",
               r"清单", r"榜单"]),
]


# 到处都是、没有检索价值的泛词
GENERIC = {
    "ai", "人工智能", "ai工具", "aigc", "科技", "干货", "干货分享", "知识分享",
    "涨知识", "教程", "热门", "推荐", "分享", "实用", "必看", "收藏", "学习",
    "抖音", "抖音小助手", "抖音科技", "上热门", "涨粉", "创作者", "vlog",
    "生活", "日常", "记录", "原创", "教学", "技巧", "方法", "教育", "好物",
    "ai新星计划", "vibecoding大赏", "程序员", "开发", "软件", "互联网",
    "大模型", "模型", "工具", "神器", "网站", "项目", "内容", "视频",
}


def _norm(s):
    return (s or "").lower()


_ASCII = re.compile(r"^[a-z0-9 .+#/-]+$")


def _count(hay, needle):
    """英文按词边界计数，中文直接子串计数。"""
    if _ASCII.match(needle):
        return len(re.findall(r"(?<![a-z0-9])" + re.escape(needle) + r"(?![a-z0-9])", hay))
    return hay.count(needle)


def classify(title, tags, transcript, min_score=6):
    """返回 (三级路径, 得分, 依据)。"""
    head = _norm(f"{title} {tags}")
    body = _norm(transcript)
    best_score, best_path, best_src = 0, None, "none"
    for l1, l2, l3, kws in TAXONOMY:
        s_head = s_body = 0
        for kw, w in kws:
            hc = _count(head, kw)
            if hc:
                s_head += w * 10 * min(hc, 2)
            bc = _count(body, kw)
            if bc:
                s_body += w * min(bc, 3)
        total = s_head + s_body
        if total > best_score:
            best_score, best_path = total, [l1, l2, l3]
            best_src = "title" if s_head >= s_body else "transcript"
    if not best_path or best_score < min_score:
        return ["其他", "未归类", "待整理"], best_score, "none"
    return best_path, best_score, best_src


def extract_terms(title, tags, transcript, topn=10):
    """抽取工具名/技术名等「可检索术语」。

    只保留有区分度的词：像「AI」「人工智能」「干货」这类到处都是的词没有检索价值，
    会被过滤掉；「Claude Code」「MCP」「RAG」「装修避坑」这种才留下。
    """
    head = _norm(f"{title} {tags}")
    body = _norm(transcript)
    scored = []
    for canon, aliases in TERMS.items():
        hit_head = sum(_count(head, a) for a in aliases)
        hit_body = sum(_count(body, a) for a in aliases)
        if hit_head or hit_body:
            scored.append((hit_head * 10 + min(hit_body, 8), canon))
    scored.sort(key=lambda x: -x[0])
    terms, low = [], set()
    for _, c in scored:
        if c.lower() in low:
            continue
        low.add(c.lower()); terms.append(c)
        if len(terms) >= topn:
            break
    # 补充原生话题：过滤泛词，且不与已有术语重复
    if len(terms) < topn:
        for t in re.split(r"[，,、\s]+", tags or ""):
            t = t.strip()
            tl = t.lower()
            if not (1 < len(t) <= 12) or tl in low:
                continue
            if tl in GENERIC or any(g == tl for g in GENERIC):
                continue
            if any(tl in x.lower() or x.lower() in tl for x in terms):
                continue
            terms.append(t); low.add(tl)
            if len(terms) >= topn:
                break
    return terms


def detect_form(title, tags, transcript):
    """判断内容形态。"""
    head = f"{title} {tags}"
    body = (transcript or "")[:1200]
    best, best_n = "经验分享", 0
    for name, pats in FORMS:
        n = 0
        for p in pats:
            n += len(re.findall(p, head)) * 3
            n += len(re.findall(p, body))
        if n > best_n:
            best, best_n = name, n
    return best
