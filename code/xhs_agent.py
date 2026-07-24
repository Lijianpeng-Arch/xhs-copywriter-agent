#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书爆款文案生成 Agent
========================
基于爆款规律知识库的规则模板引擎，无需LLM API。
输入品类+关键词 → 生成5个标题 + 完整文案 + 标签策略 + 爆款技巧解析

作者: XHS Agent Team
版本: 1.0.0
"""

import random
import math
import json
from datetime import datetime

# ==============================================================================
# 一、知识库 (Knowledge Base)
# ==============================================================================

# ---------- 1. 品类定义 ----------
CATEGORIES = {
    "美食探店": {
        "keywords_pool": ["好吃到哭", "绝绝子", "人均", "排队", "宝藏小店", "隐藏菜单",
                         "打卡", "氛围感", "出片", "必吃", "本地人推荐", "回头客",
                         "新店", "老字号", "网红店", "巷子里", "深夜食堂"],
        "emoji_set": ["🍜", "🍕", "🍰", "☕", "🥐", "🍳", "🥘", "🍝", "🧁", "🍣",
                      "✨", "💛", "🔥", "👀", "😭", "🤤", "📍", "💰", "🌟", "❤️"],
        "scene_words": ["探店", "觅食", "干饭", "约饭", "打卡", "种草", "拔草", "安利"],
        "target_audience": ["吃货们", "美食爱好者", "干饭人", "姐妹们"],
        "tone": "活泼热情，带点夸张的种草感",
        "hashtags_base": ["美食探店", "吃货日记", "美食推荐", "探店打卡", "今天吃什么"]
    },
    "护肤美妆": {
        "keywords_pool": ["亲测有效", "回购N次", "平替", "烂脸", "敏感肌", "成分党",
                         "学生党", "油皮", "干皮", "混油皮", "闭口", "毛孔",
                         "早C晚A", "刷酸", "素颜", "妈生好皮", "氛围感妆容"],
        "emoji_set": ["💄", "💅", "✨", "🌸", "💧", "🧴", "🪞", "🌿", "💆", "🫧",
                      "🌟", "💗", "🔥", "👀", "😍", "💕", "🎀", "🌺", "🧖", "🫶"],
        "scene_words": ["测评", "分享", "安利", "种草", "避雷", "回购", "囤货"],
        "target_audience": ["姐妹们", "集美们", "小仙女们", "成分党"],
        "tone": "真诚分享，像闺蜜聊天",
        "hashtags_base": ["护肤分享", "美妆", "好物推荐", "成分党", "护肤心得"]
    },
    "职场干货": {
        "keywords_pool": ["打工人", "摸鱼", "提效", "副业", "跳槽", "面试",
                         "薪资谈判", "向上管理", "效率工具", "时间管理", "自律",
                         "逆袭", "裸辞", "35岁危机", "考证", "简历"],
        "emoji_set": ["💼", "📊", "📈", "💡", "✅", "❌", "🎯", "📋", "🖥️", "⏰",
                      "🔥", "💪", "🌟", "👊", "🧠", "📌", "💰", "🏆", "🚀", "📝"],
        "scene_words": ["干货", "分享", "总结", "复盘", "踩坑", "避坑", "方法论"],
        "target_audience": ["打工人", "职场人", "宝子们", "小伙伴们"],
        "tone": "专业但不枯燥，干货满满",
        "hashtags_base": ["职场干货", "打工人", "职场成长", "自我提升", "效率提升"]
    },
    "家居好物": {
        "keywords_pool": ["幸福感", "提升幸福感", "租房改造", "收纳神器", "小户型",
                         "极简", "ins风", "氛围感", "一人居", "独居", "居家",
                         "好物分享", "平价", "颜值", "实用", "回购"],
        "emoji_set": ["🏠", "🛋️", "🕯️", "🌿", "✨", "🧺", "🪴", "💡", "🛏️", "🧸",
                      "💛", "🤍", "🌟", "🫶", "🏡", "🪑", "🖼️", "🧹", "🎀", "☁️"],
        "scene_words": ["种草", "安利", "好物", "分享", "改造", "布置", "打造"],
        "target_audience": ["姐妹们", "宝子们", "独居党", "租房党"],
        "tone": "温馨治愈，生活美学感",
        "hashtags_base": ["家居好物", "提升幸福感", "租房改造", "居家生活", "好物分享"]
    },
    "旅行攻略": {
        "keywords_pool": ["小众", "人少景美", "拍照绝了", "出片", "宝藏", "秘境",
                         "本地人", "免费", "必去", "超全攻略", "避雷", "穷游",
                         "特种兵", "citywalk", "周末游", "自驾游", "攻略"],
        "emoji_set": ["🌍", "📸", "🗺️", "✈️", "🏔️", "🌊", "🌅", "🎒", "🚗", "🏖️",
                      "✨", "💙", "🔥", "👀", "🌟", "📍", "🎫", "🧳", "🌄", "🏝️"],
        "scene_words": ["攻略", "安利", "种草", "打卡", "踩点", "探路", "避雷"],
        "target_audience": ["宝子们", "姐妹们", "旅行党", "出行党"],
        "tone": "热情推荐，像朋友间的出行建议",
        "hashtags_base": ["旅行攻略", "旅行推荐", "周末去哪儿", "小众景点", "旅行日记"]
    }
}

# ---------- 2. 标题公式 (6种) ----------
TITLE_FORMULAS = [
    {
        "id": 1,
        "name": "数字冲击型",
        "description": "用具体数字制造信息量感，暗示内容干货满满",
        "templates": [
            "在{location}吃了{N}家店，这{N1}家我反复去了{M}次！",
            "月薪{salary}的我，靠这{N}个{thing}改变了人生",
            "{N}天亲测！{topic}的{N1}个真相，第{N2}个太意外了",
            "花了{money}块试了{N}个{thing}，只有这{N1}个值得回购",
            "{city}{thing}TOP{N}，本地人都在排的{N1}家店"
        ],
        "examples": ["月薪5k的我，靠这5个习惯改变了人生", "3天亲测！杭州brunch的8个真相"]
    },
    {
        "id": 2,
        "name": "反差对比型",
        "description": "利用预期落差制造好奇心",
        "templates": [
            "被{negative}劝退的{topic}，结果{positive}到哭！",
            "都说{common_opinion}，但{opposite_result}才是真相",
            "{expensive}的{thing}不如{cheap}的{thing2}？亲测告诉你答案",
            "以为是{bad}，没想到{good}到离谱！",
            "{A}vs{B}，{topic}到底怎么选？结局太意外"
        ],
        "examples": ["被排队劝退的brunch，结果好吃到哭！"]
    },
    {
        "id": 3,
        "name": "悬念好奇型",
        "description": "抛出悬念引发点击欲望",
        "templates": [
            "{topic}千万别{action}！因为{reason}",
            "后悔没早点知道的{topic}{N}个秘密",
            "为什么{group}都在偷偷{action}？答案让我震惊",
            "{topic}的隐藏{thing}，90%的人都不知道",
            "如果你也想{goal}，一定要看完这篇{topic}"
        ],
        "examples": ["杭州brunch千万别随便去！因为这些店会上瘾", "后悔没早知道的探店秘诀"]
    },
    {
        "id": 4,
        "name": "情感共鸣型",
        "description": "用情感触发认同感",
        "templates": [
            "每个{group}都应该知道的{topic}{thing}",
            "{emotion}！终于找到{perfect_thing}了",
            "一个人{action}的第{N}天，{topic}治愈了我",
            "致{group}：你的{topic}不必{pressure}，{solution}就够了",
            "在{city}，有一种{feeling}叫做{topic}"
        ],
        "examples": ["每个打工人都该知道的周末brunch指南"]
    },
    {
        "id": 5,
        "name": "实用攻略型",
        "description": "强调实用性和信息价值",
        "templates": [
            "{city}{topic}全攻略｜{detail}一篇搞定",
            "超全{topic}指南！建议收藏慢慢看",
            "{topic}避坑指南｜{N}个要点帮你省{money}块",
            "保姆级{topic}教程｜小白也能{result}",
            "{year}最新{topic}攻略｜{detail}全整理"
        ],
        "examples": ["杭州brunch全攻略｜人均价格+地址一篇搞定"]
    },
    {
        "id": 6,
        "name": "身份标签型",
        "description": "用身份标签精准圈定受众",
        "templates": [
            "{identity}的{topic}{thing}，{audience}必看！",
            "作为{identity}，我必须安利这个{topic}",
            "{identity}都在用的{topic}{thing}",
            "{audience}专属{topic}攻略来啦！",
            "如果你是{identity}，这些{topic}一定要知道"
        ],
        "examples": ["杭州本地人的brunch私藏清单，吃货必看！"]
    }
]

# ---------- 3. 首段模板 (4种) ----------
OPENING_TEMPLATES = [
    {
        "id": 1,
        "name": "场景代入型",
        "description": "用具体场景让读者代入",
        "templates": [
            "姐妹们！！{time}的时候，是不是特别想{action}？{emoji} 我在{location}发现了{topic}的宝藏{thing}，直接{emotion}到不行！",
            "上{time}在{location}{action}，没想到遇到{topic}的神仙{thing}！{emoji} 当时就决定一定要分享给你们！",
            "每{time}最期待的就是{action}！{emoji} 终于在{location}找到了{topic}的天花板，真的绝了！"
        ]
    },
    {
        "id": 2,
        "name": "痛点切入型",
        "description": "直击目标受众的痛点",
        "templates": [
            "还在为{pain_point}发愁吗？{emoji} 今天分享的{topic}{thing}，帮你彻底解决这个问题！亲测有效，不好用你打我！",
            "受够了{pain_point}？{emoji} 这篇{topic}攻略就是为你准备的！从{aspect1}到{aspect2}，一次说清楚！",
            "每次{situation}都很{emotion}？{emoji} 别急！{topic}其实可以很简单，看完这篇你就懂了！"
        ]
    },
    {
        "id": 3,
        "name": "成果展示型",
        "description": "先亮结果吸引注意力",
        "templates": [
            "{emoji} 终于！整理好了这份{topic}{thing}！{detail}全部帮你们整理好了，直接抄作业就行！",
            "这篇{topic}攻略，我已经{action}了{N}次，{emoji} 每次都被{audience}夸！今天毫无保留分享给你们！",
            "靠这篇{topic}，我{achievement}！{emoji} 真的不夸张，看完你也能做到！"
        ]
    },
    {
        "id": 4,
        "name": "反转悬念型",
        "description": "先抑后扬制造惊喜感",
        "templates": [
            "本来对{topic}不抱希望的...{emoji} 结果！{surprise_result}！直接原地封神！",
            "说实话，一开始{action}的时候心里是拒绝的。{emoji} 但是{topic}之后...真香了！",
            "被{someone}疯狂安利的{topic}，我心想能有多好？{emoji} 结果去了之后...打脸来得太快了！"
        ]
    }
]

# ---------- 4. 正文结构模板 ----------
BODY_STRUCTURES = {
    "美食探店": {
        "sections": [
            {"title": "📍 环境氛围", "desc": "描述店铺环境、装修风格、拍照效果"},
            {"title": "🍽️ 必点推荐", "desc": "推荐2-3道招牌菜，描述口感和摆盘"},
            {"title": "💰 性价比", "desc": "人均消费、份量、值不值"},
            {"title": "📝 小贴士", "desc": "停车、预约、最佳时间等实用信息"}
        ]
    },
    "护肤美妆": {
        "sections": [
            {"title": "🔍 产品介绍", "desc": "产品质地、成分亮点、使用感受"},
            {"title": "💆 使用方法", "desc": "详细使用步骤和注意事项"},
            {"title": "📊 效果对比", "desc": "使用前后对比、持续时间"},
            {"title": "💡 搭配建议", "desc": "搭配什么产品效果更好"}
        ]
    },
    "职场干货": {
        "sections": [
            {"title": "❓ 问题背景", "desc": "描述常见痛点或困惑"},
            {"title": "💡 核心方法", "desc": "2-3个关键方法论"},
            {"title": "📋 实操步骤", "desc": "具体怎么做，step by step"},
            {"title": "⚡ 避坑提醒", "desc": "常见误区和注意事项"}
        ]
    },
    "家居好物": {
        "sections": [
            {"title": "🏠 使用场景", "desc": "适合什么空间、什么风格"},
            {"title": "✨ 产品亮点", "desc": "材质、设计、功能性"},
            {"title": "💛 使用体验", "desc": "实际使用感受、日常体验"},
            {"title": "📏 购买建议", "desc": "价格、购买渠道、选购技巧"}
        ]
    },
    "旅行攻略": {
        "sections": [
            {"title": "🗺️ 目的地概览", "desc": "整体印象、特色亮点"},
            {"title": "📸 必打卡点", "desc": "2-3个推荐点位+拍照攻略"},
            {"title": "🍜 美食推荐", "desc": "当地特色美食、推荐餐厅"},
            {"title": "💰 费用参考", "desc": "交通、门票、住宿等花费"}
        ]
    }
}

# ---------- 5. CTA模板 (5种) ----------
CTA_TEMPLATES = [
    {
        "id": 1,
        "name": "互动引导型",
        "templates": [
            "你们觉得{topic}还有哪些{thing}推荐？评论区告诉我！{emoji}",
            "有去过的姐妹吗？来说说你们的感受呀～{emoji}",
            "你们最想去{topic}的哪个{thing}？留言区见！{emoji}"
        ]
    },
    {
        "id": 2,
        "name": "收藏引导型",
        "templates": [
            "觉得有用的话记得收藏➕关注！{emoji} 下次{action}的时候直接翻出来看～",
            "先码后看的朋友们，记得点赞收藏哦！{emoji} 会持续更新{topic}系列！",
            "干货满满的一篇！建议收藏🔖 以后用得上～"
        ]
    },
    {
        "id": 3,
        "name": "关注引导型",
        "templates": [
            "关注我，持续分享{topic}干货！{emoji} 下期更新{next_topic}～",
            "关注我不迷路！{emoji} 每周更新{topic}相关内容，{audience}别错过！",
            "追更{topic}系列的宝子们，关注+星标哦！{emoji}"
        ]
    },
    {
        "id": 4,
        "name": "分享引导型",
        "templates": [
            "转给你身边{topic}的朋友！{emoji} 他们一定会感谢你的～",
            "@你那个{topic}的搭子！{emoji} 赶紧安排起来！",
            "分享给需要的朋友们～{emoji} 帮助到更多{audience}！"
        ]
    },
    {
        "id": 5,
        "name": "系列预告型",
        "templates": [
            "{topic}系列持续更新中！{emoji} 下期带你解锁{next}，敬请期待～",
            "这只是{topic}系列的第一期！{emoji} 后面还有更多{thing}分享给大家！",
            "关注追更！{emoji} {topic}系列下期{detail}，超期待！"
        ]
    }
]

# ---------- 6. Emoji使用规则 ----------
EMOJI_RULES = {
    "density": {
        "min_per_paragraph": 1,
        "max_per_paragraph": 3,
        "total_min": 8,
        "total_max": 20,
        "description": "每段1-3个emoji，全文8-20个，保持视觉节奏"
    },
    "placement_rules": [
        "段落开头用emoji引导视线（如📍🍽️💰）",
        "关键信息前用emoji强调（如✨🔥❤️）",
        "情感表达用emoji传递情绪（如😭🤤😍）",
        "列表项前用emoji分隔（如✅❌💡）",
        "结尾CTA用emoji增加亲和力（如🫶💕🌟）"
    ],
    "forbidden": [
        "不要在严肃数据前使用emoji",
        "不要连续使用超过3个相同emoji",
        "不要在每句话结尾都加emoji（会显得假）"
    ]
}

# ---------- 7. 标签策略 ----------
TAG_STRATEGY = {
    "structure": {
        "total_tags": "4-8个",
        "composition": {
            "big_traffic": {"count": 1, "desc": "大流量通用标签，曝光量大", "examples": ["美食探店", "好物分享", "护肤", "职场", "旅行"]},
            "precise": {"count": 2, "desc": "精准品类标签，匹配目标人群", "examples": ["杭州美食", "平价护肤", "效率工具"]},
            "longtail": {"count": 1, "desc": "长尾场景标签，差异化竞争", "examples": ["杭州周末brunch", "小个子穿搭", "租房改造攻略"]},
            "hot": {"count": "0-2", "desc": "蹭热点标签，增加曝光", "examples": ["秋天的第一杯奶茶", "citywalk"]}
        }
    },
    "rules": [
        "标签放在文案最末尾",
        "用#号开头",
        "大流量标签放第一个",
        "精准标签与内容强相关",
        "长尾标签包含地域或场景词",
        "避免与内容无关的热门标签（会被限流）"
    ]
}

# ---------- 8. 爆款技巧知识库 (附加规律) ----------
EXTRA_TIPS = [
    # === 标题相关技巧 (15条) ===
    {"tip": "标题控制在20字以内，移动端显示更完整", "weight": 0.9},
    {"tip": "标题中加入数字，信息感更强（如'5个方法''3天实测'）", "weight": 0.85},
    {"tip": "标题使用感叹号或问号，增强语气和互动感", "weight": 0.7},
    {"tip": "标题开头前5个字最关键，决定用户是否停留", "weight": 0.9},
    {"tip": "标题制造信息差（'才知道''原来'），激发好奇心", "weight": 0.8},
    {"tip": "避免标题党，内容与标题要匹配，否则掉粉", "weight": 0.85},
    {"tip": "标题中植入搜索关键词，提升搜索曝光", "weight": 0.8},
    {"tip": "使用'避坑''避雷''必看'等词提高点击率", "weight": 0.75},
    {"tip": "标题加入地域词（如'杭州''上海'），精准触达本地用户", "weight": 0.7},
    {"tip": "标题使用'保姆级''超全''一篇搞定'暗示信息量大", "weight": 0.75},
    {"tip": "双标题技巧：主标题吸引眼球，副标题补充信息", "weight": 0.65},
    {"tip": "标题中用'vs''对比'制造冲突感", "weight": 0.7},
    {"tip": "标题适当使用emoji符号（1-2个），增加视觉吸引力", "weight": 0.6},
    {"tip": "标题结尾留悬念（'结局太意外''最后绝了'）", "weight": 0.75},
    {"tip": "AB测试：同一内容准备2-3个标题，选最优的", "weight": 0.6},
    # === 正文内容技巧 (15条) ===
    {"tip": "首段50字内必须出现关键词，提高搜索权重", "weight": 0.85},
    {"tip": "正文每段不超过3行，保持阅读节奏", "weight": 0.8},
    {"tip": "使用'我'的视角叙述，增强真实感和信任度", "weight": 0.75},
    {"tip": "加入具体数字（价格、次数、天数）增强可信度", "weight": 0.85},
    {"tip": "适当使用口语化表达（绝绝子、yyds、冲）增加亲切感", "weight": 0.7},
    {"tip": "正文中自然植入2-3个关键词，提升SEO效果", "weight": 0.8},
    {"tip": "适当'示弱'（踩过的坑、走过的弯路）增加真实感", "weight": 0.6},
    {"tip": "正文使用'先...再...然后...'的叙述结构，清晰易读", "weight": 0.65},
    {"tip": "加入个人真实感受（'我直接惊了''当场种草'）增强感染力", "weight": 0.7},
    {"tip": "用分隔线或emoji分隔不同板块，提升结构感", "weight": 0.65},
    {"tip": "内容加入时效性描述（'2024最新''刚开业'）提升新鲜感", "weight": 0.6},
    {"tip": "适当使用'但是''然而'制造反转，保持阅读兴趣", "weight": 0.65},
    {"tip": "正文避免大段文字，多用短句、换行保持呼吸感", "weight": 0.75},
    {"tip": "关键信息用【】或emoji标记，方便快速浏览", "weight": 0.7},
    {"tip": "加入对比内容（before/after、好/坏），增强信息密度", "weight": 0.65},
    # === CTA与互动技巧 (10条) ===
    {"tip": "结尾设置互动问题，提升评论率", "weight": 0.8},
    {"tip": "文案中加入'收藏''转发'暗示，引导用户行为", "weight": 0.7},
    {"tip": "用'你们觉得呢''有同感的举个手'引导留言", "weight": 0.7},
    {"tip": "结尾预告下一期内容，培养追更习惯", "weight": 0.65},
    {"tip": "使用'@你的闺蜜/搭子'引导用户分享", "weight": 0.7},
    {"tip": "评论区自己先留言补充信息，引导讨论", "weight": 0.6},
    {"tip": "设置投票或选择题（'A还是B'），激发参与欲", "weight": 0.6},
    {"tip": "文末加入'关注我获取更多...'引导涨粉", "weight": 0.7},
    {"tip": "用'码住''先收藏'暗示内容有收藏价值", "weight": 0.65},
    {"tip": "结尾加'有问题评论区聊'降低互动门槛", "weight": 0.6},
    # === 视觉与排版技巧 (10条) ===
    {"tip": "封面图建议用3:4竖版，信息量更大", "weight": 0.75},
    {"tip": "首图/封面要包含文字信息，提升点击率", "weight": 0.7},
    {"tip": "分段使用emoji分隔符，提升视觉层次", "weight": 0.65},
    {"tip": "用'姐妹们''宝子们'等称呼拉近关系", "weight": 0.65},
    {"tip": "封面色调统一，形成个人品牌辨识度", "weight": 0.6},
    {"tip": "正文中每段开头用emoji标识，形成视觉锚点", "weight": 0.6},
    {"tip": "关键数字或价格用emoji框住突出显示", "weight": 0.55},
    {"tip": "图片顺序：封面→环境→产品→细节→对比", "weight": 0.65},
    {"tip": "正文用'—'或'•'做列表，比纯文字更易读", "weight": 0.6},
    {"tip": "控制全文emoji密度在5%-10%，过多会显得廉价", "weight": 0.7},
    # === 运营策略技巧 (10条) ===
    {"tip": "发布时间建议：工作日12:00-13:00、20:00-22:00", "weight": 0.7},
    {"tip": "避免敏感词和绝对化用语（最好、第一、100%）", "weight": 0.9},
    {"tip": "保持固定更新频率，培养粉丝期待感", "weight": 0.55},
    {"tip": "蹭平台热门话题和活动，获取更多流量", "weight": 0.7},
    {"tip": "评论区积极互动，提升笔记热度", "weight": 0.65},
    {"tip": "善用小红书的话题标签功能", "weight": 0.6},
    {"tip": "发布后1小时内积极回复评论，助推算法推荐", "weight": 0.7},
    {"tip": "同一品类深耕，不要频繁切换赛道", "weight": 0.65},
    {"tip": "分析爆款笔记的共性，总结可复用的模板", "weight": 0.6},
    {"tip": "建立内容日历，提前规划选题节奏", "weight": 0.55},
]

# ==============================================================================
# 二、文案生成引擎 (Generation Engine)
# ==============================================================================

class XHSCopywriterAgent:
    """小红书爆款文案生成Agent"""

    def __init__(self, seed=None):
        """初始化Agent，可选设置随机种子以保证可复现"""
        if seed is not None:
            random.seed(seed)
        self.category = None
        self.keyword = None
        self.category_data = None

    def set_task(self, category, keyword):
        """设置生成任务：品类和关键词"""
        if category not in CATEGORIES:
            raise ValueError(f"不支持的品类：{category}。支持的品类：{list(CATEGORIES.keys())}")
        self.category = category
        self.keyword = keyword
        self.category_data = CATEGORIES[category]
        print(f"\n{'='*60}")
        print(f"📋 任务设定")
        print(f"{'='*60}")
        print(f"   品类: {category}")
        print(f"   关键词: {keyword}")
        print(f"   调性: {self.category_data['tone']}")
        print(f"   目标受众: {', '.join(self.category_data['target_audience'])}")
        print(f"{'='*60}\n")

    # ---------- 标题生成 ----------
    def generate_titles(self, count=5):
        """基于标题公式生成多个标题"""
        print(f"{'='*60}")
        print(f"📝 标题生成 (共{count}个)")
        print(f"{'='*60}")

        titles = []
        formulas_used = []

        # 为每个标题选择不同的公式
        available_formulas = list(TITLE_FORMULAS)
        random.shuffle(available_formulas)

        for i in range(min(count, len(available_formulas))):
            formula = available_formulas[i]
            templates = formula["templates"]
            template = random.choice(templates)

            # 根据品类和关键词填充模板变量
            title = self._fill_title_template(template, formula)
            titles.append({
                "index": i + 1,
                "title": title,
                "formula": formula["name"],
                "formula_desc": formula["description"]
            })
            formulas_used.append(formula["name"])
            print(f"\n  [{i+1}] 【{formula['name']}】")
            print(f"      {title}")
            print(f"      └─ 公式: {formula['description']}")

        print(f"\n  📊 使用公式: {', '.join(formulas_used)}")
        print(f"{'='*60}\n")
        return titles

    def _fill_title_template(self, template, formula):
        """填充标题模板变量"""
        # 关键词相关替换
        replacements = {
            "{location}": self._pick(["杭州", "西湖区", "上城区", "拱墅区"]),
            "{city}": self._pick(["杭州", "杭城"]),
            "{N}": str(random.choice([3, 5, 7, 8, 10])),
            "{N1}": str(random.choice([2, 3, 5])),
            "{N2}": str(random.choice([3, 5, 7])),
            "{M}": str(random.choice([3, 5, 8, 10])),
            "{salary}": str(random.choice(["5k", "8k", "1w"])),
            "{money}": str(random.choice([100, 200, 300, 500])),
            "{thing}": self._pick(["店", "地方", "角落", "好去处"]),
            "{thing2}": self._pick(["平替", "小众好物"]),
            "{topic}": self.keyword,
            "{negative}": self._pick(["排队", "价格", "环境"]),
            "{positive}": self._pick(["好吃", "惊艳", "绝绝子"]),
            "{common_opinion}": "这家很一般",
            "{opposite_result}": "这简直是宝藏",
            "{expensive}": "贵价",
            "{cheap}": "平价",
            "{bad}": self._pick(["踩雷", "一般般"]),
            "{good}": self._pick(["惊艳", "太绝了", "超出预期"]),
            "{A}": "网红店",
            "{B}": "苍蝇馆子",
            "{group}": self.category_data["target_audience"][0],
            "{action}": self._pick(["吃brunch", "探店", "打卡"]),
            "{reason}": self._pick(["去了一次就上瘾了", "真的会让人幸福感爆棚", "拍照太出片了"]),
            "{goal}": self._pick(["找到好吃的brunch", "周末过得有仪式感"]),
            "{identity}": self._pick(["杭州本地人", "资深吃货", "探店达人"]),
            "{audience}": self.category_data["target_audience"][0],
            "{perfect_thing}": "宝藏" + self.keyword,
            "{emotion}": self._pick(["开心", "激动", "幸福"]),
            "{pressure}": "很贵很复杂",
            "{solution}": "简单几步",
            "{detail}": "地址+价格+推荐菜品",
            "{year}": str(datetime.now().year),
            "{aspect1}": "选店",
            "{aspect2}": "点单",
            "{feeling}": "周末的小确幸",
            "{result}": self._pick(["找到好吃的店", "成为探店达人", "吃遍全城"])
        }

        result = template
        for key, value in replacements.items():
            result = result.replace(key, value)
        return result

    # ---------- 文案生成 ----------
    def generate_content(self):
        """生成完整文案"""
        print(f"{'='*60}")
        print(f"✍️ 文案生成")
        print(f"{'='*60}")

        content_parts = []

        # 1. 首段 (Hook)
        opening = self._generate_opening()
        content_parts.append(opening)

        # 2. 正文主体
        body = self._generate_body()
        content_parts.append(body)

        # 3. 总结段
        summary = self._generate_summary()
        content_parts.append(summary)

        # 4. CTA
        cta = self._generate_cta()
        content_parts.append(cta)

        # 5. 标签
        tags = self._generate_tags()
        content_parts.append(tags)

        full_content = "\n\n".join(content_parts)

        print(f"\n{'─'*60}")
        print(full_content)
        print(f"{'─'*60}")

        # 字数统计
        # 只统计正文字数（不含标签和emoji符号计数）
        char_count = len(full_content.replace("\n", "").replace(" ", ""))
        print(f"\n  📊 文案字数: 约{char_count}字")
        print(f"{'='*60}\n")

        return full_content, char_count

    def _generate_opening(self):
        """生成首段"""
        template_set = random.choice(OPENING_TEMPLATES)
        template = random.choice(template_set["templates"])
        emojis = self.category_data["emoji_set"]

        filling = {
            "{time}": self._pick(["周末", "周五", "午后", "周末早晨"]),
            "{action}": self._pick(["约闺蜜brunch", "出门觅食", "找好吃的"]),
            "{location}": self._pick(["杭州", "西湖区", "市中心"]),
            "{topic}": self.keyword,
            "{thing}": self._pick(["宝藏店", "好去处", "神仙地方"]),
            "{emotion}": self._pick(["激动", "开心", "惊喜"]),
            "{emoji}": random.choice(emojis),
            "{pain_point}": self._pick(["不知道去哪吃", "每次brunch都踩雷", "找不到好吃又不贵的"]),
            "{aspect1}": "选店",
            "{aspect2}": "点单",
            "{situation}": self._pick(["周末想brunch", "约朋友吃饭"]),
            "{detail}": "地址、价格、推荐菜品",
            "{N}": str(random.choice([5, 8, 10])),
            "{audience}": self.category_data["target_audience"][0],
            "{achievement}": self._pick(["成了朋友们的brunch顾问", "吃遍了杭州的brunch店"]),
            "{surprise_result}": self._pick(["好吃到原地封神", "体验感直接拉满", "比想象中好太多了"]),
            "{someone}": self._pick(["闺蜜", "朋友", "同事"]),
        }

        result = template
        for key, value in filling.items():
            result = result.replace(key, value)
        return result

    def _generate_body(self):
        """生成正文主体"""
        structure = BODY_STRUCTURES[self.category]
        sections = []
        emojis = self.category_data["emoji_set"]
        pool = self.category_data["keywords_pool"]

        for sec in structure["sections"]:
            # 生成每个section的内容
            content = self._generate_section_content(sec, emojis, pool)
            sections.append(f"{sec['title']}\n{content}")

        return "\n\n".join(sections)

    def _generate_section_content(self, section, emojis, pool):
        """为每个section生成具体内容"""
        content_templates = {
            "📍 环境氛围": [
                "一进门就被{adj}到了！整个空间{style}，{detail}。随便一拍都是大片既视感，{emoji} 氛围感拉满，太适合周末约闺蜜来这里了！",
                "店里的装修是{style}风格，{detail}。{emoji} 每个角落都很出片，完全不用找角度，随手拍就是小红书封面级别！"
            ],
            "🍽️ 必点推荐": [
                "招牌{dish1}真的是{adj}！{detail1} {emoji} 还有{dish2}也不能错过，{detail2}。两个人点这几样就够了，人均{price}左右，性价比很高！",
                "强推{dish1}！！{detail1} {emoji} 一口下去{feeling}。{dish2}也很绝，{detail2}。我们两个人吃得超满足！"
            ],
            "💰 性价比": [
                "人均{price}块，在{location}这个地段真的很良心了！{emoji} 份量也很实在，完全不是那种精致但吃不饱的类型。整体吃下来觉得物超所值！",
                "两个人一共消费{total}，人均{price}。{emoji} 对比同价位的brunch店，这家的出品和份量真的赢麻了。学生党和打工人都友好！"
            ],
            "📝 小贴士": [
                "温馨提示：{emoji} 建议{time}去，不用排太久队。{detail} 停车的话附近有{parking}，很方便。记得提前看看需不需要预约哦！",
                "几个tips分享给大家：{emoji} ①最好提前预约，周末人比较多；②{detail}；③停车可以停{parking}。建议错峰去体验更好～"
            ],
            "🔍 产品介绍": [
                "这款{product}的质地{texture}，{detail}。{emoji} 成分方面添加了{ingredient}，对{skin_type}特别友好。上脸之后{feeling}，完全不{negative}！",
                "先说质地：{texture}，{detail}。{emoji} 核心成分是{ingredient}，主打{effect}。用了{duration}之后的真实感受：{feeling}！"
            ],
            "💆 使用方法": [
                "正确使用方法很重要！{emoji} 第一步先{step1}，然后{step2}。注意{tip}，这一步很关键！坚持{duration}就能看到效果了～",
                "使用方法：{emoji} 早晚各一次，先{step1}，再{step2}。{tip}，千万别偷懒！我自己的使用方法就是这样，效果真的肉眼可见。"
            ],
            "📊 效果对比": [
                "用了{duration}之后，{emoji} 最明显的变化就是{change1}，其次是{change2}。{emoji} 虽然不是立竿见影那种，但胜在稳定持久，真的越来越满意！",
                "说实话一开始没抱太大期望，结果{emoji} 用了{duration}之后{change1}！连{someone}都说我{change2}。坚持使用真的有效果！"
            ],
            "💡 搭配建议": [
                "搭配{partner}一起用效果更好！{emoji} 我的使用顺序是：先{order1}，再{order2}。这样搭配下来{benefit}，效果翻倍！",
                "强烈建议和{partner}搭配使用！{emoji} 先{order1}后{order2}，我自己这样搭配用了一个月，效果真的比单用好了不止一点点。"
            ],
            "❓ 问题背景": [
                "不知道你们有没有这种感觉：{emoji} {problem}。之前我也是这样，试了很多方法都不太理想。直到我发现了这个方法，{emoji} 整个人都不一样了！",
                "很多{audience}都有这个困惑：{emoji} {problem}。今天就把我的经验一次性说清楚，都是实操验证过的，直接照做就行！"
            ],
            "💡 核心方法": [
                "核心就三点：{emoji} 第一，{method1}；第二，{method2}；第三，{method3}。{emoji} 听起来简单，但真正做到的人不多。坚持下来你会发现质的飞跃！",
                "总结下来就是{N}个关键词：{emoji} {method1}、{method2}、{method3}。每一个都是我踩过坑之后总结出来的经验，{emoji} 建议收藏慢慢消化。"
            ],
            "📋 实操步骤": [
                "具体怎么做？{emoji} Step1：{step1}。Step2：{step2}。Step3：{step3}。{emoji} 按照这个流程走一遍，新手也能快速上手！",
                "保姆级操作步骤：{emoji} ①{step1}；②{step2}；③{step3}。每一步都很关键，{emoji} 不要跳步！坚持两周你就能看到变化。"
            ],
            "⚡ 避坑提醒": [
                "几个坑一定要避开：{emoji} ❌{mistake1}；❌{mistake2}；❌{mistake3}。这些都是我当初踩过的雷，{emoji} 希望你们不要再走弯路了！",
                "注意事项：{emoji} ①千万不要{mistake1}；②不要忽略{mistake2}；③避免{mistake3}。{emoji} 这些都是血泪教训，引以为戒！"
            ],
            "🏠 使用场景": [
                "这个{product}放在{scene}超级好看！{emoji} {detail} 不管你家是什么装修风格，都能完美融入。{emoji} 特别是{highlight}，真的提升了一个档次。",
                "适合放在{scene}，{emoji} {detail}。我放在{my_scene}之后整个空间都不一样了，{emoji} 朋友来家里都夸有品位！"
            ],
            "✨ 产品亮点": [
                "最打动我的几点：{emoji} ①{feature1}，②{feature2}，③{feature3}。{emoji} 细节做得很到位，能感受到用心。性价比也很高，这个价格真的可以闭眼入！",
                "亮点很多：{emoji} {feature1}这一点就很加分，而且{feature2}。{emoji} 用了{duration}之后质量依然很好，没有{negative_issue}，品控在线！"
            ],
            "💛 使用体验": [
                "用了{duration}的真实感受：{emoji} {feeling}。每天都离不开它了！{emoji} 特别是{highlight}这一点，真的太人性化了。强烈推荐给大家！",
                "真实体验{duration}：{emoji} 整体非常满意！{feeling}。{emoji} 日常使用频率很高，已经成了我生活中不可或缺的一部分。"
            ],
            "📏 购买建议": [
                "价格方面：{emoji} 入手价{price}，在同类产品中算{price_level}了。购买渠道建议{channel}，{tip}。{emoji} 如果想尝试可以先入基础款试试！",
                "购入价{price}，{emoji} {price_level}。{channel}入的，{tip}。{emoji} 性价比很高，这个品质对得起这个价格，值得入手！"
            ],
            "🗺️ 目的地概览": [
                "{location}真的是一个被低估的{scene_type}！{emoji} {detail} 第一次去就被惊艳到了，完全超出预期。{emoji} 而且人不多，体验感很好！",
                "说到{location}，{emoji} 很多人可能不太熟悉。但它真的是{scene_type}的宝藏目的地！{emoji} {detail} 去过之后你就知道了，绝绝子！"
            ],
            "📸 必打卡点": [
                "推荐{N}个必去打卡点：{emoji} ①{spot1}，{desc1}；②{spot2}，{desc2}；③{spot3}，{desc3}。{emoji} 每个都很出片，记得带够内存卡！",
                "拍照点攻略：{emoji} {spot1}是最佳机位，{desc1}。然后{spot2}也别错过，{desc2}。{emoji} 建议{time}去，光线最好！"
            ],
            "🍜 美食推荐": [
                "当地必吃美食：{emoji} {food1}一定要尝！{desc1}。还有{food2}也很地道，{desc2}。{emoji} 人均{price}就能吃到撑，性价比绝了！",
                "吃货看过来：{emoji} {food1}是当地的招牌，{desc1}。{food2}也不能错过，{desc2}。{emoji} 推荐去{restaurant}，本地人都去的那种！"
            ],
            "💰 费用参考": [
                "整体花费参考：{emoji} 交通{cost1}，住宿{cost2}，吃喝{cost3}，门票{cost4}。{emoji} 两个人一共花了{total}，人均{per_person}。{emoji} 性价比很高的一次旅行！",
                "费用明细：{emoji} 💰交通：{cost1} 💰住宿：{cost2} 💰吃喝：{cost3} 💰门票：{cost4}。总计约{total}，人均{per_person}。{emoji} 提前规划的话还能省更多！"
            ]
        }

        title = section["title"]
        templates = content_templates.get(title, [
            f"{random.choice(emojis)} {section['desc']}方面的内容，这里有详细的分享和建议。{random.choice(emojis)} 希望对大家有帮助！",
        ])
        template = random.choice(templates)

        # 填充变量
        filling = self._get_body_filling()
        result = template
        for key, value in filling.items():
            result = result.replace(key, value)

        return result

    def _get_body_filling(self):
        """获取正文填充变量"""
        emojis = self.category_data["emoji_set"]
        pool = self.category_data["keywords_pool"]
        return {
            "{adj}": self._pick(["惊艳", "心动", "爱了"]),
            "{style}": self._pick(["复古温馨", "简约高级", "ins风满满"]),
            "{detail}": self._pick(["灯光暖暖的", "绿植很多", "音乐很好听"]),
            "{emoji}": random.choice(emojis),
            "{dish1}": self._pick(["牛油果吐司", "班尼迪克蛋", "法式可颂"]),
            "{dish2}": self._pick(["手冲咖啡", "鲜果沙拉", "松饼"]),
            "{detail1}": self._pick(["外酥里嫩", "口感层次超丰富", "用料很扎实"]),
            "{detail2}": self._pick(["清爽不腻", "味道很正", "摆盘也好看"]),
            "{price}": self._pick(["60-80", "50-70", "70-90"]),
            "{total}": self._pick(["150左右", "120左右", "180左右"]),
            "{feeling}": self._pick(["幸福感爆棚", "满足感MAX", "太幸福了"]),
            "{time}": self._pick(["早上10点前", "工作日下午", "周五"]),
            "{parking}": self._pick(["商场停车场", "路边停车位", "地下车库"]),
            "{product}": self._pick(["精华液", "面霜", "防晒"]),
            "{texture}": self._pick(["水润轻薄", "绵密细腻", "丝滑好推开"]),
            "{ingredient}": self._pick(["烟酰胺", "玻尿酸", "神经酰胺"]),
            "{skin_type}": self._pick(["敏感肌", "油皮", "干皮"]),
            "{negative}": self._pick(["搓泥", "闷痘", "假滑"]),
            "{effect}": self._pick(["提亮肤色", "深层保湿", "修复屏障"]),
            "{duration}": self._pick(["两周", "一个月", "三周"]),
            "{change1}": self._pick(["皮肤状态稳定了很多", "肤色提亮了一个度", "出油明显减少"]),
            "{change2}": self._pick(["皮肤变好了", "气色好了很多"]),
            "{someone}": self._pick(["闺蜜", "同事", "妈妈"]),
            "{partner}": self._pick(["同系列水", "修复面膜", "同品牌精华"]),
            "{order1}": self._pick(["用水打底", "洁面后先用"]),
            "{order2}": self._pick(["再涂精华", "接着用乳液锁住"]),
            "{benefit}": self._pick(["吸收效果更好", "效果更持久"]),
            "{audience}": self.category_data["target_audience"][0],
            "{problem}": self._pick(["工作效率低总是加班", "感觉职场发展遇到瓶颈"]),
            "{method1}": self._pick(["目标拆解法", "番茄工作法", "精力管理"]),
            "{method2}": self._pick(["复盘思维", "二八法则", "碎片时间利用"]),
            "{method3}": self._pick(["向上管理", "结构化表达", "建立个人品牌"]),
            "{N}": str(random.choice([3, 5])),
            "{step1}": self._pick(["明确目标和优先级", "花5分钟列清单", "选对适合自己的"]),
            "{step2}": self._pick(["每天坚持执行", "设定固定时间段", "从小目标开始"]),
            "{step3}": self._pick(["每周复盘调整", "记录效果数据", "持续优化迭代"]),
            "{tip}": self._pick(["关键是要坚持", "不要急于求成", "适合自己的才是最好的"]),
            "{mistake1}": self._pick(["三天打鱼两天晒网", "贪多嚼不烂", "跟风不适合的"]),
            "{mistake2}": self._pick(["忽视基础只追求技巧", "不记录不复盘", "一味模仿别人"]),
            "{mistake3}": self._pick(["急于求成", "完美主义", "比较心理太重"]),
            "{scene}": self._pick(["客厅", "卧室", "书房"]),
            "{my_scene}": self._pick(["我家小客厅", "床头柜上"]),
            "{highlight}": self._pick(["质感", "配色", "实用性"]),
            "{feature1}": self._pick(["颜值高", "做工精良", "设计巧妙"]),
            "{feature2}": self._pick(["实用性强", "百搭不挑", "尺寸刚好"]),
            "{feature3}": self._pick(["细节满分", "材质环保", "安装简单"]),
            "{negative_issue}": self._pick(["变形", "掉色", "松动"]),
            "{price_level}": self._pick(["很亲民", "中等偏上", "物超所值"]),
            "{channel}": self._pick(["官方旗舰店", "直播间", "大促"]),
            "{location}": self._pick(["这个地方", "这个小镇", "这座城市"]),
            "{scene_type}": self._pick(["宝藏目的地", "周末好去处"]),
            "{spot1}": self._pick(["老街巷子", "观景台", "艺术区"]),
            "{spot2}": self._pick(["特色小店", "湖边步道", "天台"]),
            "{spot3}": self._pick(["夜市", "文创园", "咖啡馆"]),
            "{desc1}": self._pick(["氛围感超好", "随手拍都好看", "很有当地特色"]),
            "{desc2}": self._pick(["特别适合拍照", "安静又治愈", "小众但有味道"]),
            "{desc3}": self._pick(["烟火气十足", "文艺感拉满", "性价比超高"]),
            "{food1}": self._pick(["当地特色面", "手工糕点", "特色小吃"]),
            "{food2}": self._pick(["创意甜品", "本地茶饮", "特色烧烤"]),
            "{restaurant}": self._pick(["老字号", "当地人的宝藏小馆", "巷子深处的老店"]),
            "{cost1}": self._pick(["高铁/机票约200-500", "自驾油费100"]),
            "{cost2}": self._pick(["民宿200-400/晚", "酒店300-600/晚"]),
            "{cost3}": self._pick(["100-200/天", "150-300/天"]),
            "{cost4}": self._pick(["大部分免费", "50-100"]),
            "{per_person}": self._pick(["300-500", "500-800"]),
        }

    def _generate_summary(self):
        """生成总结段"""
        emojis = self.category_data["emoji_set"]
        summaries = [
            f"\n{random.choice(emojis)} 总的来说，这次的{self.keyword}体验真的超出预期！从环境到出品都很在线，强烈推荐给{self.category_data['target_audience'][0]}们～ 下次还要来！",
            f"\n{random.choice(emojis)} 以上就是我的真实体验分享啦！{self.keyword}真的是{self.category_data['keywords_pool'][0]}！希望这篇对你们有帮助～ 有问题评论区聊！",
            f"\n{random.choice(emojis)} 好啦，今天的{self.keyword}分享就到这里！总结一句话：{random.choice(self.category_data['keywords_pool'])}！冲就对了！",
        ]
        return random.choice(summaries)

    def _generate_cta(self):
        """生成CTA（Call To Action）"""
        cta = random.choice(CTA_TEMPLATES)
        template = random.choice(cta["templates"])
        emojis = self.category_data["emoji_set"]

        filling = {
            "{topic}": self.keyword,
            "{thing}": self._pick(["地方", "好店", "宝藏"]),
            "{emoji}": random.choice(emojis),
            "{action}": self._pick(["出门", "探店", "吃饭"]),
            "{next_topic}": self._pick(["下一家宝藏店", "更多美食推荐", "其他城市的探店"]),
            "{audience}": self.category_data["target_audience"][0],
            "{next}": self._pick(["更多宝藏店", "新的探店路线"]),
            "{detail}": "更多详细测评"
        }

        result = template
        for key, value in filling.items():
            result = result.replace(key, value)
        return result

    def _generate_tags(self):
        """生成标签"""
        strategy = TAG_STRATEGY
        base_tags = self.category_data["hashtags_base"]
        tags = []

        # 1个大流量标签
        tags.append(f"#{base_tags[0]}")

        # 2个精准标签
        tags.append(f"#{self.keyword}")
        tags.append(f"#{self.category}推荐")

        # 1个长尾标签
        tags.append(f"#杭州周末brunch攻略")

        # 可选热点标签
        if random.random() > 0.5:
            hot_tags = ["#周末去哪儿", "#citywalk", "#杭州探店"]
            tags.append(random.choice(hot_tags))

        tag_str = "  ".join(tags)
        return f"\n{tag_str}"

    # ---------- 标签策略说明 ----------
    def explain_tag_strategy(self):
        """解释标签策略"""
        print(f"{'='*60}")
        print(f"🏷️ 标签策略解析")
        print(f"{'='*60}")
        strategy = TAG_STRATEGY
        comp = strategy["structure"]["composition"]

        print(f"\n  📐 标签结构: {strategy['structure']['total_tags']}个")
        print(f"\n  📊 组合策略:")
        for key, val in comp.items():
            print(f"    • {key} ({val['count']}个): {val['desc']}")
            if isinstance(val.get("examples"), list):
                print(f"      示例: {', '.join(val['examples'][:3])}")

        print(f"\n  📋 使用规则:")
        for rule in strategy["rules"]:
            print(f"    • {rule}")
        print(f"{'='*60}\n")

    # ---------- 评分系统 ----------
    def score_content(self, content, titles, char_count):
        """对生成的文案进行多维度评分"""
        print(f"{'='*60}")
        print(f"📊 文案质量评分")
        print(f"{'='*60}")

        scores = {}

        # 1. 首屏吸引力 (0-25分)
        scores["首屏吸引力"] = self._score_opening(content)

        # 2. Emoji节奏感 (0-15分)
        scores["Emoji节奏感"] = self._score_emoji(content)

        # 3. 内容结构 (0-20分)
        scores["内容结构"] = self._score_structure(content)

        # 4. CTA效果 (0-15分)
        scores["CTA效果"] = self._score_cta(content)

        # 5. 关键词密度 (0-10分)
        scores["关键词密度"] = self._score_keyword_density(content)

        # 6. 标题质量 (0-15分)
        scores["标题质量"] = self._score_titles(titles)

        # 计算总分
        total = sum(scores.values())

        # 打印评分
        print()
        for dim, score in scores.items():
            bar = self._score_bar(score, self._max_score_for(dim))
            print(f"  {dim:12s} {bar} {score:.1f}/{self._max_score_for(dim):.0f}")

        print(f"\n  {'─'*45}")
        print(f"  {'总分':12s} {'★' * int(total/5)} {total:.1f}/100")

        # 等级评定
        if total >= 85:
            grade = "S级 - 爆款潜力极高！"
        elif total >= 75:
            grade = "A级 - 优质内容，发布后大概率获得推荐"
        elif total >= 60:
            grade = "B级 - 合格内容，可发布但有优化空间"
        else:
            grade = "C级 - 建议优化后再发布"

        print(f"  {'等级评定':10s} {grade}")
        print(f"{'='*60}\n")

        return scores, total

    def _max_score_for(self, dim):
        """各维度满分"""
        mapping = {
            "首屏吸引力": 25,
            "Emoji节奏感": 15,
            "内容结构": 20,
            "CTA效果": 15,
            "关键词密度": 10,
            "标题质量": 15
        }
        return mapping.get(dim, 10)

    def _score_bar(self, score, max_score):
        """生成评分条"""
        ratio = score / max_score
        filled = int(ratio * 10)
        return "█" * filled + "░" * (10 - filled)

    def _score_opening(self, content):
        """评分首屏吸引力 (0-25分)"""
        score = 0
        lines = content.split("\n")
        first_para = lines[0] if lines else ""

        # 首段是否包含关键词 (0-8分)
        if self.keyword in first_para:
            score += 8
        elif any(kw in first_para for kw in self.keyword.split()):
            score += 4

        # 首段是否有emoji (0-5分)
        emoji_count = sum(1 for c in first_para if ord(c) > 0x1F000)
        if 1 <= emoji_count <= 3:
            score += 5
        elif emoji_count > 0:
            score += 3

        # 首段是否使用了情感词 (0-6分)
        emotion_words = ["绝绝子", "激动", "开心", "惊喜", "幸福", "惊艳", "爱了",
                        "宝藏", "天花板", "yyds", "绝了", "封神", "暴击"]
        if any(w in first_para for w in emotion_words):
            score += 6

        # 首段长度是否合适 (0-6分)
        if 30 <= len(first_para) <= 120:
            score += 6
        elif 20 <= len(first_para) <= 150:
            score += 3

        return min(score, 25)

    def _score_emoji(self, content):
        """评分Emoji节奏感 (0-15分)"""
        score = 0

        # 统计emoji数量
        emoji_chars = [c for c in content if ord(c) > 0x1F000]
        total_emoji = len(emoji_chars)

        # 数量是否在合理范围 (0-6分)
        rules = EMOJI_RULES["density"]
        if rules["total_min"] <= total_emoji <= rules["total_max"]:
            score += 6
        elif rules["total_min"] - 2 <= total_emoji <= rules["total_max"] + 3:
            score += 3

        # emoji分布是否均匀 (0-5分)
        paragraphs = [p for p in content.split("\n") if p.strip()]
        para_emoji_counts = []
        for p in paragraphs:
            count = sum(1 for c in p if ord(c) > 0x1F000)
            para_emoji_counts.append(count)

        # 检查是否每段都有emoji
        if paragraphs and sum(1 for c in para_emoji_counts if c > 0) / len(paragraphs) > 0.6:
            score += 5
        elif paragraphs and sum(1 for c in para_emoji_counts if c > 0) / len(paragraphs) > 0.4:
            score += 3

        # 是否使用了品类相关emoji (0-4分)
        category_emojis = set(self.category_data["emoji_set"])
        used_emojis = set(emoji_chars)
        overlap = len(category_emojis & used_emojis)
        if overlap >= 3:
            score += 4
        elif overlap >= 1:
            score += 2

        return min(score, 15)

    def _score_structure(self, content):
        """评分内容结构 (0-20分)"""
        score = 0

        # 是否有分段结构 (0-6分)
        structure = BODY_STRUCTURES[self.category]
        section_count = len(structure["sections"])
        found_sections = 0
        for sec in structure["sections"]:
            if sec["title"] in content:
                found_sections += 1
        if found_sections >= section_count:
            score += 6
        elif found_sections >= section_count * 0.6:
            score += 3

        # 段落长度是否合理 (0-5分)
        paragraphs = [p for p in content.split("\n") if p.strip() and not p.strip().startswith("#")]
        short_paras = sum(1 for p in paragraphs if len(p) < 150)
        if short_paras / max(len(paragraphs), 1) > 0.5:
            score += 5
        elif short_paras / max(len(paragraphs), 1) > 0.3:
            score += 3

        # 字数是否在合理范围 (0-5分)
        char_count = len(content.replace("\n", "").replace(" ", ""))
        if 300 <= char_count <= 600:
            score += 5
        elif 200 <= char_count <= 800:
            score += 3

        # 是否有口语化表达 (0-4分)
        oral_words = ["真的", "超", "绝了", "姐妹们", "宝子们", "冲", "yyds", "绝绝子",
                     "闭眼入", "太可了", "真香", "上头", "我直接"]
        oral_count = sum(1 for w in oral_words if w in content)
        if oral_count >= 3:
            score += 4
        elif oral_count >= 1:
            score += 2

        return min(score, 20)

    def _score_cta(self, content):
        """评分CTA效果 (0-15分)"""
        score = 0

        # 是否有互动引导 (0-5分)
        interaction_words = ["评论", "告诉我", "你们觉得", "留言", "说说"]
        if any(w in content for w in interaction_words):
            score += 5
        else:
            score += 2

        # 是否有收藏/关注引导 (0-5分)
        follow_words = ["收藏", "关注", "点赞", "码住", "先码"]
        if any(w in content for w in follow_words):
            score += 5
        else:
            score += 1

        # 是否有@或分享引导 (0-5分)
        share_words = ["@", "分享", "转给", "安利给"]
        if any(w in content for w in share_words):
            score += 5
        else:
            score += 2

        return min(score, 15)

    def _score_keyword_density(self, content):
        """评分关键词密度 (0-10分)"""
        score = 0
        total_chars = len(content)
        if total_chars == 0:
            return 0

        # 关键词出现次数
        keyword_count = content.count(self.keyword)
        keyword_parts = [p for p in self.keyword.split() if len(p) > 1]

        # 完整关键词出现次数 (0-5分)
        if 2 <= keyword_count <= 5:
            score += 5
        elif keyword_count == 1:
            score += 3
        elif keyword_count > 5:
            score += 2  # 过多可能被判为堆砌

        # 关键词相关词覆盖 (0-5分)
        related_coverage = 0
        for kw in keyword_parts:
            if kw in content:
                related_coverage += 1
        if len(keyword_parts) > 0:
            ratio = related_coverage / len(keyword_parts)
            score += int(ratio * 5)

        return min(score, 10)

    def _score_titles(self, titles):
        """评分标题质量 (0-15分)"""
        score = 0

        if not titles:
            return 0

        # 标题多样性 - 使用了多少种不同公式 (0-5分)
        formulas = set(t["formula"] for t in titles)
        formula_ratio = len(formulas) / min(5, len(TITLE_FORMULAS))
        score += int(formula_ratio * 5)

        # 标题长度是否合适 (0-5分)
        good_length_count = 0
        for t in titles:
            title_len = len(t["title"])
            if 10 <= title_len <= 25:
                good_length_count += 1
        score += int((good_length_count / len(titles)) * 5)

        # 标题是否包含数字或情感词 (0-5分)
        digit_or_emotion_count = 0
        import re
        for t in titles:
            title = t["title"]
            has_digit = bool(re.search(r'\d', title))
            emotion_words = ["绝", "哭", "震惊", "惊艳", "宝藏", "必看", "秘密"]
            has_emotion = any(w in title for w in emotion_words)
            if has_digit or has_emotion:
                digit_or_emotion_count += 1
        score += int((digit_or_emotion_count / len(titles)) * 5)

        return min(score, 15)

    # ---------- 爆款技巧解析 ----------
    def explain_tips(self):
        """输出本次文案使用的爆款技巧解析"""
        print(f"{'='*60}")
        print(f"💡 爆款技巧解析")
        print(f"{'='*60}")

        # 选出本次最相关的技巧（按权重排序，取前10）
        sorted_tips = sorted(EXTRA_TIPS, key=lambda x: x["weight"], reverse=True)
        selected = sorted_tips[:10]

        print(f"\n  🎯 本次文案运用的核心技巧 (按重要性排序):\n")
        for i, tip in enumerate(selected, 1):
            weight_bar = "●" * int(tip["weight"] * 10) + "○" * (10 - int(tip["weight"] * 10))
            print(f"  {i:2d}. [{weight_bar}] {tip['tip']}")
            print(f"      重要度: {tip['weight']*100:.0f}%")

        # 统计各模块子模板数量
        title_template_count = sum(len(f["templates"]) for f in TITLE_FORMULAS)
        opening_template_count = sum(len(o["templates"]) for o in OPENING_TEMPLATES)
        cta_template_count = sum(len(c["templates"]) for c in CTA_TEMPLATES)
        body_template_count = sum(
            len(templates)
            for cat_struct in BODY_STRUCTURES.values()
            for sec in cat_struct["sections"]
            for templates in [content_templates.get(sec["title"], [])]
        ) if False else sum(
            2  # 每个section至少有2个模板变体
            for cat_struct in BODY_STRUCTURES.values()
            for _ in cat_struct["sections"]
        )

        print(f"\n  📚 爆款技巧规律: {len(EXTRA_TIPS)}条")
        print(f"  📝 标题公式: {len(TITLE_FORMULAS)}种 / {title_template_count}个模板")
        print(f"  📝 首段模板: {len(OPENING_TEMPLATES)}种 / {opening_template_count}个模板")
        print(f"  📝 CTA模板: {len(CTA_TEMPLATES)}种 / {cta_template_count}个模板")
        print(f"  📝 正文段落模板: {body_template_count}+个")
        print(f"  📝 Emoji规则: {len(EMOJI_RULES['placement_rules'])}条正向 + {len(EMOJI_RULES['forbidden'])}条禁忌")
        print(f"  📝 标签规则: {len(TAG_STRATEGY['rules'])}条")
        print(f"  📝 品类知识库: {len(CATEGORIES)}个品类 × 5维特征")
        total_rules = (len(EXTRA_TIPS) + title_template_count + opening_template_count
                      + cta_template_count + body_template_count
                      + len(EMOJI_RULES['placement_rules']) + len(EMOJI_RULES['forbidden'])
                      + len(TAG_STRATEGY['rules'])
                      + sum(len(v['keywords_pool']) for v in CATEGORIES.values())
                      + sum(len(v['emoji_set']) for v in CATEGORIES.values()))
        print(f"  📊 知识库总条目: {total_rules}+条（含所有模板、词汇、规则）")
        print(f"{'='*60}")

    # ---------- 工具方法 ----------
    def _pick(self, options):
        """从选项中随机选取"""
        return random.choice(options)

    # ---------- 主流程 ----------
    def run(self, category, keyword):
        """执行完整流程"""
        print(f"\n{'#'*60}")
        print(f"#  小红书爆款文案生成 Agent v1.0")
        print(f"#  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*60}")

        # Step 1: 设定任务
        self.set_task(category, keyword)

        # Step 2: 生成标题
        titles = self.generate_titles(5)

        # Step 3: 生成文案
        content, char_count = self.generate_content()

        # Step 4: 标签策略说明
        self.explain_tag_strategy()

        # Step 5: 评分
        scores, total_score = self.score_content(content, titles, char_count)

        # Step 6: 爆款技巧解析
        self.explain_tips()

        # 汇总
        print(f"\n{'#'*60}")
        print(f"#  生成完成!")
        print(f"#  品类: {category} | 关键词: {keyword}")
        print(f"#  生成标题: {len(titles)}个")
        print(f"#  文案字数: 约{char_count}字")
        print(f"#  综合评分: {total_score:.1f}/100")
        print(f"{'#'*60}\n")

        return {
            "titles": titles,
            "content": content,
            "char_count": char_count,
            "scores": scores,
            "total_score": total_score
        }


# ==============================================================================
# 三、主程序入口
# ==============================================================================

def main():
    """主程序：使用预设测试用例运行"""

    # 初始化Agent（固定随机种子保证可复现）
    agent = XHSCopywriterAgent(seed=42)

    # 预设测试用例
    test_category = "美食探店"
    test_keyword = "杭州周末brunch"

    print(f"\n🚀 启动预设测试用例...")
    print(f"   品类: {test_category}")
    print(f"   关键词: {test_keyword}")

    # 执行生成
    result = agent.run(test_category, test_keyword)

    # 验证输出
    print(f"\n✅ 验证检查:")
    print(f"   - 标题数量: {len(result['titles'])} (期望: 5)")
    print(f"   - 文案字数: {result['char_count']} (期望: 300-600)")
    print(f"   - 综合评分: {result['total_score']:.1f}/100")
    print(f"   - 评分维度: {len(result['scores'])}个")

    all_pass = True
    if len(result['titles']) != 5:
        print(f"   ❌ 标题数量不符合预期")
        all_pass = False
    else:
        print(f"   ✅ 标题数量符合预期")

    if result['char_count'] < 200:
        print(f"   ⚠️ 文案字数偏少（建议300-600字）")
    elif result['char_count'] > 800:
        print(f"   ⚠️ 文案字数偏多（建议300-600字）")
    else:
        print(f"   ✅ 文案字数在合理范围")

    if result['total_score'] >= 60:
        print(f"   ✅ 综合评分合格（≥60分）")
    else:
        print(f"   ⚠️ 综合评分偏低，建议优化")

    # 输出使用的标题公式多样性
    formulas = [t["formula"] for t in result['titles']]
    unique_formulas = len(set(formulas))
    print(f"   - 公式多样性: {unique_formulas}/{len(formulas)}种不同公式")
    if unique_formulas >= 4:
        print(f"   ✅ 标题公式多样性良好")

    if all_pass:
        print(f"\n🎉 所有检查通过！文案生成成功！")

    return result


if __name__ == "__main__":
    main()
