"""在 DeepSeek Harness Web GUI 的「轨迹」中加载更早历史，定位真实 AI 协作节点并截图。

依赖：Xvfb :99 已启动、127.0.0.1:3081 autologin 代理可用、ImageMagick import。
输出：evidence/ai-5-01.png ~ ai-5-04.png
"""
import os
import subprocess
import sys

from playwright.sync_api import sync_playwright

TARGETS = [
    ("01", "你现在是本项目的全权开发负责人"),
    ("02", "T03 错选显示答案与解析"),
    ("03", "21 passed, 0 failed"),
    ("04", "galleries-adaptive-signed-transition"),
]
MAX_BATCHES = 40


def body_text(pg):
    try:
        return pg.inner_text("body")
    except Exception:
        return ""


with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/usr/bin/google-chrome",
        headless=False,
        args=["--no-sandbox", "--window-size=1520,1320", "--window-position=0,0", "--hide-scrollbars"],
        env={**os.environ, "DISPLAY": ":99"},
    )
    ctx = browser.new_context(no_viewport=True, locale="zh-CN")
    pg = ctx.new_page()
    pg.goto("http://127.0.0.1:3081/", wait_until="load")
    pg.wait_for_timeout(3500)
    pg.get_by_role("button", name="搜索会话").click()
    pg.wait_for_timeout(1800)
    pg.get_by_text("进行中", exact=True).first.evaluate(
        """e=>{let n=e;for(let i=0;i<6&&n;i++){if(n.tagName==='BUTTON'||n.getAttribute('role')==='button'||n.tagName==='A'){n.click();return;}n=n.parentElement;}e.closest('li,div')?.click();}"""
    )
    pg.wait_for_timeout(4500)
    pg.get_by_text("轨迹", exact=True).first.click()
    pg.wait_for_timeout(3000)

    found = {}
    for b in range(MAX_BATCHES):
        text = body_text(pg)
        for num, anchor in TARGETS:
            if num not in found and anchor in text:
                found[num] = b
                print(f"[batch {b}] found {num} anchor={anchor}", flush=True)
        if len(found) == len(TARGETS):
            break
        btn = pg.get_by_text("加载更早的历史", exact=True)
        if btn.count() == 0:
            print("no load-more button, stop", flush=True)
            break
        try:
            btn.first.evaluate("e=>e.closest('button,a,[role=button]')?.click() || e.click()")
        except Exception as exc:
            print("click err", str(exc)[:100], flush=True)
            break
        pg.wait_for_timeout(2200)
        print(f"[batch {b}] loaded; body_len={len(body_text(pg))}", flush=True)

    for num, anchor in TARGETS:
        loc = pg.get_by_text(anchor, exact=False)
        n = loc.count()
        print(f"{num} {anchor!r} count={n}", flush=True)
        if n == 0:
            print(f"MISS {num}", flush=True)
            continue
        el = loc.last
        try:
            el.scroll_into_view_if_needed(timeout=12000)
        except Exception as exc:
            print("scroll fail", num, str(exc)[:100], flush=True)
            continue
        pg.wait_for_timeout(500)
        out = f"evidence/ai-5-{num}.png"
        subprocess.run(["import", "-display", ":99", "-window", "root", out], check=True)
        print("saved", out, flush=True)

    ctx.close()
    browser.close()
