# 小红书爆款文案 Agent

输入主题（品类 + 关键词 + 详情），5 秒输出 5 个候选标题 + 完整文案 + 6 维度评分。

## 第一次使用（Clone 之后照做）

按下面 4 步走，2 分钟跑起来：

### 第 1 步：确认有 Python

打开命令行（Windows 按 `Win+R` 输入 `cmd`，Mac 打开"终端"），输入：

```bash
python --version
```

- 显示 `Python 3.7.x` 或更高 → 跳过第 2 步，直接第 3 步
- 提示"不是内部命令" → [去 python.org 下载](https://www.python.org/downloads/) ，**安装时务必勾选 `Add Python to PATH`**

### 第 2 步：把项目下到本地

点 GitHub 仓库页右上角绿色 `Code` 按钮 → `Download ZIP`，解压到你想要的目录。

### 第 3 步：双击启动

| 系统 | 操作 |
|------|------|
| Windows | 双击 `webapp/start.cmd` |
| Mac / Linux | 终端进入 `webapp/` 目录执行 `python3 start.py` |

启动成功会**自动打开浏览器**（端口被占会自动换到 8001-8020 之间的空闲端口，看终端提示）。

### 第 4 步：选模式

- **不填 Key**：默认走**离线模式**，内置 5 个爆款公式 + 6 维度评分，5 秒出文案
- **填 Key 走 AI 模式**（推荐，文案更自然）：点页面右上角 ⚙️ 设置 → 粘贴你的 API Key → 点「自动识别并保存」→ 点「测试连接」成功即可

> 支持 DeepSeek / Moonshot Kimi / 智谱 GLM / 通义千问 / MiniMax / OpenAI，**自动识别厂商**，不用手动选。
> Key 只保存在你本地的 `webapp/config.json`，**不会上传任何地方**（这个文件已被 `.gitignore` 排除）。

## 5 秒上手

### Windows 用户

双击 `webapp/start.cmd`

### Mac / Linux 用户

```bash
cd webapp
python3 start.py
```

浏览器自动打开。

### 命令行版

```bash
cd code
python3 xhs_agent.py
```

## 🆘 启动报错？这 3 个坑最常见

### 坑 1：双击 `start.cmd` 弹个黑窗一闪而过

**原因**：电脑没装 Python，或安装时没勾选「Add Python to PATH」。

**解决**：
1. 打开浏览器，输入 `python --version` 验证：能显示版本 → 已装好；显示"不是内部命令" → 没装
2. 没装 → 去 [python.org/downloads](https://www.python.org/downloads/) 下载安装
3. 安装时**务必勾选第一个界面底部的「Add Python to PATH」**，否则 cmd 找不到 python
4. 安装完重新双击 `start.cmd`

### 坑 2：双击后黑窗一直停在那里没动

正常现象：在「等待服务就绪…」这步会停 2-3 秒，等本地网页服务起来。**别关掉它**，等浏览器自动弹出即可。关掉 = 关掉整个服务。

### 坑 3：浏览器没自动打开

手动打开浏览器，地址栏输入 `http://127.0.0.1:8001/`（端口可能不是 8001，看启动黑窗里的「访问地址」一行）。

> 端口自动选 8001-8020 之间的空闲端口，被占用时会自动换一个。

## 支持的品类

- 美食探店
- 护肤美妆
- 职场干货
- 家居好物
- 旅行攻略

每个品类有专属的爆款规律词典、词汇库、标题公式。

## 三种模式

| 模式 | 效果 |
|---|---|
| **LLM 模式** | 走真模型，文案更自然、个性化 |
| **离线模式** | 走知识库 + 规则引擎，5 标题公式 + 405 字文案 + 91/100 评分 |
| **命令行模式** | `python3 xhs_agent.py`，离线引擎 |

## 文件结构

```
项目B-小红书文案Agent/
├── README.md
├── 使用说明.md
├── Agent设计方案.md
├── 爆款规律分析文档.md        ← 5 品类爆款规律提炼
├── 竞品分析.md                ← 主流文案 Agent 对比
├── 演示案例.md
├── webapp/
│   ├── start.py / start.cmd   ← 一键启动
│   ├── server.py
│   ├── index.html
│   └── test_webapp.log
└── code/
    ├── xhs_agent.py
    └── test_output.log
```

## 依赖

仅 Python 3.7+ 标准库。

## 验证

| 项目 | 状态 |
|---|---|
| 一键启动 | ✅ 8001-8020 端口自动选择 |
| 命令行运行 | ✅ exit 0，5 标题 + 405 字 + 91 分 |
| 网页 API | ✅ 5 标题 + 评分 83 |

## License

MIT

## 关于作者

由李建鹏设计开发 · 作品集主页：https://lijianpeng-arch.github.io/