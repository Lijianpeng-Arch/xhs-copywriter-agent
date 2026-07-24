#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书爆款文案 Agent - 本地网站版后端
======================================
仅使用 Python 标准库，无需任何第三方依赖。
功能：静态服务 + 配置管理 + LLM 厂商自动识别 + 文案生成（LLM / 离线规则引擎双模式）
"""

import contextlib
import io
import json
import os
import re
import socket
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser


def open_app_window(url):
    """以应用窗口模式打开页面：免疫浏览器"恢复上次会话"设置，永远只开一个干净窗口。
    优先 Edge / Chrome 的 --app 模式；都找不到时回退系统默认浏览器。"""
    import subprocess
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]
    for exe in candidates:
        try:
            if os.path.exists(exe):
                subprocess.Popen([exe, "--app=" + url])
                return
        except Exception:
            continue
    try:
        webbrowser.open(url)
    except Exception:
        pass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
CODE_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "code"))

CATEGORIES = ["美食探店", "护肤美妆", "职场干货", "家居好物", "旅行攻略"]

# 六维度评分满分值（与离线规则引擎保持一致）
SCORE_MAX = {
    "首屏吸引力": 25,
    "Emoji节奏感": 15,
    "内容结构": 20,
    "CTA效果": 15,
    "关键词密度": 10,
    "标题质量": 15,
}

PROVIDERS = [
    {"name": "DeepSeek", "base_url": "https://api.deepseek.com/v1"},
    {"name": "Moonshot Kimi", "base_url": "https://api.moonshot.cn/v1"},
    {"name": "智谱GLM", "base_url": "https://open.bigmodel.cn/api/paas/v4"},
    {"name": "通义千问", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"},
    {"name": "MiniMax", "base_url": "https://api.minimaxi.com/v1"},
    {"name": "MiniMax(国际版)", "base_url": "https://api.minimax.io/v1"},
    {"name": "OpenAI", "base_url": "https://api.openai.com/v1"},
]

# SSL 上下文（部分环境证书不完整时也能尽量工作）
_SSL_CTX = ssl.create_default_context()


# ==============================================================================
# 配置读写
# ==============================================================================

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def mask_key(key):
    if not key:
        return ""
    if len(key) <= 8:
        return key[:2] + "****"
    return key[:4] + "****" + key[-4:]


# ==============================================================================
# LLM 网关
# ==============================================================================

def _http_json(url, headers=None, payload=None, timeout=10, method=None):
    """发起 HTTP 请求，返回 (状态码, 解析后的JSON 或 None, 原始文本)"""
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"))
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(text), text
            except Exception:
                return resp.status, None, text
    except urllib.error.HTTPError as e:
        try:
            text = e.read().decode("utf-8", errors="replace")
        except Exception:
            text = ""
        return e.code, None, text
    except Exception as e:
        return -1, None, str(e)


def detect_provider(api_key):
    """自动识别厂商：多线程并发请求各厂商 /models 接口"""
    # 智谱 Key 中间含 '.'，优先尝试
    providers = list(PROVIDERS)
    if "." in api_key:
        providers.sort(key=lambda p: 0 if p["name"] == "智谱GLM" else 1)

    result = {"provider": None, "base_url": None, "models": []}
    lock = threading.Lock()

    def probe(p):
        status, data, _ = _http_json(
            p["base_url"] + "/models",
            headers={"Authorization": "Bearer " + api_key},
            timeout=6,
        )
        if status == 200 and isinstance(data, dict):
            models = []
            for item in data.get("data", [])[:30]:
                if isinstance(item, dict) and item.get("id"):
                    models.append(item["id"])
            with lock:
                if result["provider"] is None:
                    result["provider"] = p["name"]
                    result["base_url"] = p["base_url"]
                    result["models"] = models

    threads = [threading.Thread(target=probe, args=(p,), daemon=True) for p in providers]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=8)

    if result["provider"]:
        return {"ok": True, **result}
    return {"ok": False, "error": "未能识别该 Key 所属厂商，可在设置里手动填写接口地址（所有厂商探测均失败）"}


def call_llm(cfg, system_prompt, user_prompt, max_tokens=2000):
    """统一 LLM 调用（OpenAI 兼容格式）。返回 {ok, reply} 或 {ok:False, error}"""
    base_url = cfg.get("base_url", "").rstrip("/")
    api_key = cfg.get("api_key", "")
    model = cfg.get("model", "")
    if not (base_url and api_key and model):
        return {"ok": False, "error": "LLM 配置不完整，请检查设置"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.9,
    }
    start = time.time()
    status, data, raw = _http_json(
        base_url + "/chat/completions",
        headers={"Authorization": "Bearer " + api_key},
        payload=payload,
        timeout=300,
    )
    # 部分模型 max_tokens 上限较低（如 DeepSeek 8192）：超限被 400 拒绝时自动降档重试
    while status == 400 and raw and "max_tokens" in raw.lower() and payload.get("max_tokens", 0) > 4096:
        payload["max_tokens"] = payload["max_tokens"] // 2
        status, data, raw = _http_json(
            base_url + "/chat/completions",
            headers={"Authorization": "Bearer " + api_key},
            payload=payload,
            timeout=300,
        )
    latency = int((time.time() - start) * 1000)
    if status == 200 and isinstance(data, dict):
        try:
            reply = data["choices"][0]["message"]["content"]
            # 思考型模型（MiniMax-M系列 / DeepSeek-R1 等）会附带 <think>...</think> 思考块，统一剥离
            reply = re.sub(r"<think>.*?(</think>|$)", "", reply, flags=re.S).strip()
            return {"ok": True, "reply": reply, "latency_ms": latency}
        except Exception:
            return {"ok": False, "error": "模型返回格式异常，无法解析"}
    if status == 401:
        return {"ok": False, "error": "API Key 无效或已过期（401），请检查后重新配置"}
    if status == 429:
        return {"ok": False, "error": "请求过于频繁或额度不足（429），请稍后再试"}
    if status == -1:
        return {"ok": False, "error": "网络连接失败：%s" % raw[:120]}
    return {"ok": False, "error": "调用模型失败（HTTP %s）：%s" % (status, raw[:150])}


# ==============================================================================
# 文案生成：LLM 模式
# ==============================================================================

SYSTEM_PROMPT = """你是一位粉丝10w+的小红书资深博主，深谙爆款笔记创作规律。请严格按用户要求输出 JSON。

【爆款标题公式库】（5个备选标题必须使用不同公式，并在 formula 字段标注公式名）
1. 数字冲击型：用具体数字制造信息量感，如「3天亲测！XX的8个真相」
2. 反差对比型：利用预期落差制造好奇心，如「被排队劝退的XX，结果好吃到哭」
3. 悬念好奇型：抛出悬念引发点击，如「XX千万别随便去！因为会上瘾」
4. 情感共鸣型：用情感触发认同，如「每个打工人都该知道的XX指南」
5. 实用攻略型：强调实用价值，如「XX全攻略｜一篇搞定」
6. 身份标签型：精准圈定受众，如「本地人私藏的XX清单，吃货必看」

【标题要求】20字以内，前5字抓人，可含1个emoji，植入搜索关键词，避免绝对化用语（最好/第一/100%）。

【正文要求】
- 300-500字，第一人称真实分享口吻，口语化（可用"绝绝子/闭眼入/冲"等）
- 首段50字内出现主题关键词，带钩子（场景代入/痛点切入/成果展示/反转悬念）
- 正文按品类结构分段：每段一个小标题（emoji开头，如「📍 环境氛围」），段落不超过3行
- emoji密度：每段1-3个，全文8-20个，段落开头做视觉锚点
- 结尾必须有CTA（评论引导/收藏暗示/关注转化/分享引导之一）
- 正文中不要出现标签

【标签要求】5-8个：1个大流量词 + 2-3个精准品类词 + 1-2个长尾场景词（含地域/场景）+ 可选热点词。

【评分要求】对生成的文案按6个维度自评（整数）：
- 首屏吸引力(满分25)：首段是否含关键词、emoji、情感词、长度合适
- Emoji节奏感(满分15)：数量8-20、分布均匀、贴合品类
- 内容结构(满分20)：分段清晰、段落短、字数300-600、口语化
- CTA效果(满分15)：有互动/收藏关注/分享引导
- 关键词密度(满分10)：主题词出现2-5次不堆砌
- 标题质量(满分15)：公式多样、长度10-25字、含数字或情感词

【输出格式】只输出一个 JSON 对象，不要输出任何其他文字、不要用 markdown 代码块包裹：
{"titles":[{"title":"...","formula":"数字冲击型"},...共5个],"content":"正文（用\\n换行）","tags":["标签1","标签2",...不带#号],"scores":{"首屏吸引力":0,"Emoji节奏感":0,"内容结构":0,"CTA效果":0,"关键词密度":0,"标题质量":0}}"""


def build_user_prompt(category, topic, details):
    prompt = "品类：%s\n主题关键词：%s\n" % (category, topic)
    if details:
        prompt += "补充说明：%s\n" % details
    prompt += "\n请为该主题生成一套小红书爆款文案（5个不同公式的备选标题 + 1篇正文 + 标签 + 6维度自评分），严格按系统提示的 JSON 格式输出。"
    return prompt


def extract_json(text):
    """从模型输出中提取 JSON 对象"""
    if not text:
        return None
    text = text.strip()
    # 去掉 markdown 代码块包裹
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        pass
    # 尝试截取第一个 { 到最后一个 }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            return None
    return None


def normalize_llm_result(data, category, topic):
    """校验并规整 LLM 输出为标准结构；缺项时抛异常"""
    titles_raw = data.get("titles") or []
    titles = []
    formulas = ["数字冲击型", "反差对比型", "悬念好奇型", "情感共鸣型", "实用攻略型", "身份标签型"]
    for i, t in enumerate(titles_raw[:5]):
        if isinstance(t, dict) and t.get("title"):
            titles.append({
                "index": i + 1,
                "title": str(t["title"]).strip(),
                "formula": str(t.get("formula", formulas[i % len(formulas)])),
                "formula_desc": "",
            })
    if len(titles) < 3:
        raise ValueError("模型返回的有效标题不足")
    content = str(data.get("content", "")).strip()
    if len(content) < 50:
        raise ValueError("模型返回的正文过短")
    tags = [str(t).lstrip("#").strip() for t in (data.get("tags") or []) if str(t).strip()]
    if not tags:
        tags = [category, topic]
    scores_raw = data.get("scores") or {}
    scores = {}
    for dim, mx in SCORE_MAX.items():
        try:
            v = int(float(scores_raw.get(dim, 0)))
        except Exception:
            v = 0
        scores[dim] = max(0, min(v, mx))
    return {
        "titles": titles,
        "content": content,
        "tags": tags,
        "scores": scores,
        "total_score": sum(scores.values()),
    }


def generate_with_llm(cfg, category, topic, details):
    """LLM 模式生成：JSON 解析失败重试一次，再失败返回错误（由调用方降级）"""
    user_prompt = build_user_prompt(category, topic, details)
    last_err = None
    for attempt in range(2):
        resp = call_llm(cfg, SYSTEM_PROMPT, user_prompt, max_tokens=8192)
        if not resp["ok"]:
            return resp  # 网络/鉴权错误直接返回
        data = extract_json(resp["reply"])
        if data is None:
            last_err = "模型未按 JSON 格式输出（第%d次尝试）" % (attempt + 1)
            continue
        try:
            result = normalize_llm_result(data, category, topic)
            result["source"] = "llm"
            return {"ok": True, "data": result}
        except Exception as e:
            last_err = "模型输出校验失败：%s" % e
            continue
    return {"ok": False, "error": last_err or "模型输出解析失败"}


# ==============================================================================
# 文案生成：离线规则引擎模式
# ==============================================================================

_agent_module = None
_agent_import_err = None


def get_offline_agent_class():
    global _agent_module, _agent_import_err
    if _agent_module is not None:
        return _agent_module
    if _agent_import_err is not None:
        return None
    try:
        if CODE_DIR not in sys.path:
            sys.path.insert(0, CODE_DIR)
        import xhs_agent
        _agent_module = xhs_agent.XHSCopywriterAgent
        return _agent_module
    except Exception as e:
        _agent_import_err = str(e)
        return None


def split_content_and_tags(content):
    """把离线引擎输出的完整文案拆成 正文 和 标签列表（标签在末尾的 # 开头行）"""
    lines = content.split("\n")
    tags = []
    body_lines = []
    for line in lines:
        found = re.findall(r"#([^\s#]+)", line)
        if found and line.strip().startswith("#"):
            tags.extend(found)
        else:
            body_lines.append(line)
    body = "\n".join(body_lines).strip()
    return body, tags


def generate_offline(category, topic):
    AgentCls = get_offline_agent_class()
    if AgentCls is None:
        return {"ok": False, "error": "离线规则引擎加载失败：%s" % (_agent_import_err or "未知错误")}
    try:
        agent = AgentCls()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            agent.set_task(category, topic)
            titles = agent.generate_titles(5)
            full_content, char_count = agent.generate_content()
            scores, total_score = agent.score_content(full_content, titles, char_count)
        body, tags = split_content_and_tags(full_content)
        return {"ok": True, "data": {
            "titles": titles,
            "content": body,
            "tags": tags,
            "scores": {k: round(v, 1) for k, v in scores.items()},
            "total_score": round(total_score, 1),
            "source": "offline",
        }}
    except Exception as e:
        return {"ok": False, "error": "离线引擎生成失败：%s" % e}


# ==============================================================================
# HTTP 服务
# ==============================================================================

class Handler(BaseHTTPRequestHandler):
    server_version = "XHSAgentWeb/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("[web] %s\n" % (fmt % args))

    # ---------- 工具 ----------
    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
        except Exception:
            length = 0
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    # ---------- GET ----------
    def do_GET(self):
        try:
            if self.path == "/" or self.path == "/index.html":
                self._serve_index()
            elif self.path == "/api/status":
                cfg = load_config()
                has_key = bool(cfg.get("api_key") and cfg.get("base_url") and cfg.get("model"))
                self._send_json({
                    "ok": True,
                    "has_key": has_key,
                    "provider": cfg.get("provider", ""),
                    "model": cfg.get("model", ""),
                    "mode": "llm" if has_key else "offline",
                })
            elif self.path == "/api/config":
                cfg = load_config()
                self._send_json({
                    "ok": True,
                    "config": {
                        "api_key": mask_key(cfg.get("api_key", "")),
                        "provider": cfg.get("provider", ""),
                        "base_url": cfg.get("base_url", ""),
                        "model": cfg.get("model", ""),
                    }
                })
            else:
                self._send_json({"ok": False, "error": "接口不存在"}, status=404)
        except Exception as e:
            self._send_json({"ok": False, "error": "服务器内部错误：%s" % e}, status=500)

    def _serve_index(self):
        path = os.path.join(BASE_DIR, "index.html")
        if not os.path.exists(path):
            self._send_json({"ok": False, "error": "index.html 不存在"}, status=404)
            return
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ---------- POST ----------
    def do_POST(self):
        try:
            if self.path == "/api/config":
                self._handle_save_config()
            elif self.path == "/api/detect":
                self._handle_detect()
            elif self.path == "/api/test":
                self._handle_test()
            elif self.path == "/api/generate":
                self._handle_generate()
            elif self.path == "/api/config/clear":
                if os.path.exists(CONFIG_PATH):
                    os.remove(CONFIG_PATH)
                self._send_json({"ok": True})
            else:
                self._send_json({"ok": False, "error": "接口不存在"}, status=404)
        except Exception as e:
            self._send_json({"ok": False, "error": "服务器内部错误：%s" % e}, status=500)

    def _handle_save_config(self):
        body = self._read_body()
        cfg = load_config()
        api_key = str(body.get("api_key", "")).strip()
        if api_key and "****" not in api_key:  # 非脱敏占位符才更新
            cfg["api_key"] = api_key
        for field in ("provider", "base_url", "model"):
            val = str(body.get(field, "")).strip()
            if val:
                cfg[field] = val
        save_config(cfg)
        self._send_json({"ok": True, "mode": "llm" if cfg.get("api_key") else "offline"})

    def _handle_detect(self):
        body = self._read_body()
        api_key = str(body.get("api_key", "")).strip()
        if not api_key:
            self._send_json({"ok": False, "error": "请先输入 API Key"})
            return
        self._send_json(detect_provider(api_key))

    def _handle_test(self):
        cfg = load_config()
        if not (cfg.get("api_key") and cfg.get("base_url") and cfg.get("model")):
            self._send_json({"ok": False, "error": "尚未配置完整的 LLM 信息（Key/接口地址/模型）"})
            return
        resp = call_llm(cfg, "你是测试助手", "回复：你好", max_tokens=300)  # 思考型模型的think块也占token
        if resp["ok"]:
            self._send_json({"ok": True, "latency_ms": resp["latency_ms"], "reply": resp["reply"][:50]})
        else:
            self._send_json(resp)

    def _handle_generate(self):
        body = self._read_body()
        category = str(body.get("category", "")).strip()
        topic = str(body.get("topic", "")).strip()
        details = str(body.get("details", "")).strip()
        if category not in CATEGORIES:
            self._send_json({"ok": False, "error": "品类无效，仅支持：%s" % "、".join(CATEGORIES)})
            return
        if not topic:
            self._send_json({"ok": False, "error": "请输入主题关键词，例如「杭州周末brunch」"})
            return

        cfg = load_config()
        has_key = bool(cfg.get("api_key") and cfg.get("base_url") and cfg.get("model"))
        if has_key:
            result = generate_with_llm(cfg, category, topic, details)
            if result["ok"]:
                result["data"]["category"] = category
                result["data"]["topic"] = topic
                self._send_json({"ok": True, **result["data"]})
                return
            # LLM 失败 → 降级离线，并告知原因
            offline = generate_offline(category, topic)
            if offline["ok"]:
                offline["data"]["category"] = category
                offline["data"]["topic"] = topic
                offline["data"]["fallback_reason"] = result.get("error", "LLM 调用失败")
                self._send_json({"ok": True, **offline["data"]})
            else:
                self._send_json({"ok": False, "error": "LLM 失败：%s；离线降级也失败：%s" % (result.get("error"), offline.get("error"))})
            return
        # 离线模式
        offline = generate_offline(category, topic)
        if offline["ok"]:
            offline["data"]["category"] = category
            offline["data"]["topic"] = topic
            self._send_json({"ok": True, **offline["data"]})
        else:
            self._send_json(offline)


# ==============================================================================
# 启动
# ==============================================================================

def find_free_port():
    for port in range(8001, 8021):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return None


def main():
    port = find_free_port()
    if port is None:
        print("[错误] 8001-8020 端口均被占用，请关闭其他程序后重试")
        sys.exit(1)
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = "http://127.0.0.1:%d/" % port
    print("=" * 56)
    print("  小红书爆款文案 Agent · 本地网站版")
    print("=" * 56)
    print("  访问地址: %s" % url)
    print("  未配置 API Key 时将使用内置离线规则引擎")
    print("  按 Ctrl+C 停止服务")
    print("=" * 56)
    threading.Timer(1.0, lambda: open_app_window(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")


if __name__ == "__main__":
    main()
