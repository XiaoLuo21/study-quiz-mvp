"""把真实会话日志的片段渲染为 HTML 并截图，用于 AI 过程记录（数据来自 ~/.dsh 会话 JSONL）。"""
import json, datetime, html, subprocess, sys, os

ROOT = "/root/QuizLab"
SRC = "/tmp/sess.jsonl"
rows = [json.loads(l) for l in open(SRC) if l.strip()]
BYSEQ = {r.get("seq"): r for r in rows}

def ts(ms):
    return datetime.datetime.fromtimestamp(ms/1000, datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")

def esc(s):
    return html.escape(s).replace("\n", "<br>")

def clip(s, n):
    return s if len(s) <= n else s[:n] + f"\n…（此处截断，全文 {len(s)} 字，完整记录见 evidence/session/）"

def block(r, outlen=900):
    t = r["type"]; d = r.get("data", {})
    tm = ts(r["time"])
    if t == "user/message":
        txt = "".join(c.get("text", "") for c in d.get("content", []))
        kind = d.get("source", {}).get("kind")
        if kind in ("agent-instructions", "user-approval"):
            return ""
        label = {"goal": "用户任务（goal）", "user-approval": "系统提示", "agent-instructions": "工作区规范"}.get(kind, "用户")
        return f'<div class="ev user"><div class="meta"><b>{label}</b> · <code>{tm} UTC</code></div><div class="bubble">{esc(clip(txt, 3400))}</div></div>'
    if t == "assistant/message":
        msg = d["message"]; txt = "".join(c.get("text", "") for c in msg.get("content", []) if c.get("type") == "text")
        calls = [c for c in msg.get("content", []) if c.get("type") == "tool-call"]
        h = f'<div class="ev ai"><div class="meta"><b>AI · DeepSeek Harness</b> · deepseek/deepseek-v4.1-flash · <code>{tm} UTC</code></div>'
        if txt.strip():
            h += f'<div class="bubble">{esc(clip(txt, 1200))}</div>'
        for c in calls:
            h += f'<div class="call"><span class="tag">{esc(c["name"])}</span> <code>{esc(clip(c["arguments"], 500))}</code></div>'
        return h + "</div>"
    if t == "tool/result":
        txt = "".join(c.get("text", "") for c in d["message"].get("content", []))
        return f'<div class="ev tool"><div class="meta">工具输出 · <code>{tm} UTC</code></div><pre>{esc(clip(txt, outlen))}</pre></div>'
    return ""

def page(title, range_lo, range_hi, outlen=900):
    evs = [r for r in rows if range_lo <= r.get("seq", -1) <= range_hi and r["type"] in ("user/message", "assistant/message", "tool/result")]
    body = "\n".join(block(r, outlen) for r in evs)
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<style>
body{{margin:0;background:#f6f5f1;color:#1c2620;font-family:"Noto Sans CJK SC","Source Han Sans SC",system-ui,sans-serif;font-size:13px;line-height:1.55}}
.top{{background:#22352b;color:#f3f1ea;padding:14px 22px}}
.top h1{{margin:0;font-size:16px;font-weight:600;letter-spacing:.3px}}
.top .sub{{opacity:.72;font-size:11.5px;margin-top:4px;font-family:ui-monospace,Menlo,monospace}}
.wrap{{padding:16px 22px 26px}}
.ev{{margin:10px 0;border-radius:8px;padding:10px 12px;background:#fff;border:1px solid #e3e0d6}}
.ev.user{{border-left:4px solid #2f493c;background:#fbfaf6}}
.ev.ai{{border-left:4px solid #ac6a4b}}
.ev.tool{{border-left:4px solid #8a9490;background:#fbfbf9}}
.meta{{font-size:11px;color:#6c746f;margin-bottom:6px}}
.meta code{{font-size:10.5px}}
.bubble{{white-space:normal}}
.call{{margin-top:8px;background:#f2f0e8;border:1px solid #e0dccd;border-radius:6px;padding:7px 9px;font-family:ui-monospace,Menlo,monospace;font-size:11px;word-break:break-all}}
.tag{{display:inline-block;background:#2f493c;color:#fff;border-radius:4px;padding:1px 6px;font-size:10.5px;margin-right:6px}}
pre{{margin:6px 0 0;white-space:pre-wrap;word-break:break-all;font-family:ui-monospace,Menlo,monospace;font-size:11px;background:#f4f2ea;border-radius:6px;padding:8px}}
</style></head><body>
<div class="top"><h1>{html.escape(title)}</h1>
<div class="sub">DeepSeek Harness · session 9c48a017-4e90-4ac4-8b9d-9ad101f995c5 · /root/QuizLab · 原始会话日志渲染 · seq {range_lo}–{range_hi}</div></div>
<div class="wrap">{body}</div></body></html>"""

PAGES = [
 ("r1", "AI-第5周-01　需求阅读与执行计划（用户原始任务 → AI 首轮计划）", 18, 32, 380),
 ("r2", "AI-第5周-02　自动化 QA：编写 Playwright 脚本并首轮运行", 160, 203, 420),
 ("r3", "AI-第5周-03　公网 HTTPS 地址复测：21/21 全部通过", 285, 306, 900),
 ("r4", "AI-第5周-04　部署探测：GitHub 无凭据、cloudflared 快速隧道 404", 222, 254, 420),
]
for name, title, lo, hi, ol in PAGES:
    p = f"{ROOT}/evidence/ai-5-{name[-1]}.html".replace("ai-5-r", "ai-5-")
    open(p, "w").write(page(title, lo, hi, ol))
    print("wrote", p, len(open(p).read()))

# 截图
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 1400, "height": 980}, device_scale_factor=1.1)
    for name, *_ in PAGES:
        n = name[-1]
        html_path = f"{ROOT}/evidence/ai-5-{n}.html"
        pg.goto("file://" + html_path)
        pg.wait_for_timeout(400)
        h = pg.evaluate("document.body.scrollHeight")
        pg.set_viewport_size({"width": 1400, "height": min(h, 2400)})
        pg.wait_for_timeout(200)
        pg.screenshot(path=f"{ROOT}/evidence/ai-5-{n}.png")
        print("shot", n, h)
    b.close()
