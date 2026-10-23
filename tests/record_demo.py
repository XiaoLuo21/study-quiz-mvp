"""录制 ≤90 秒真实演示视频：首页 → 选题库 → 完成答题 → 成绩分析 → 错题重练。

用法：.venv/bin/python tests/record_demo.py [URL]
输出：evidence/quizlab-demo.webm（Playwright 原始录制）+ evidence/quizlab-demo.mp4（如可转码）
"""
import shutil
import sys
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8090/"
ROOT = Path(__file__).resolve().parent.parent
EVID = ROOT / "evidence"
RAW = EVID / "_video_raw"
if RAW.exists():
    shutil.rmtree(RAW)
RAW.mkdir(parents=True)

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/usr/bin/google-chrome",
        headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars"],
    )
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 800},
        record_video_dir=str(RAW),
        record_video_size={"width": 1280, "height": 800},
        locale="zh-CN",
        device_scale_factor=1,
    )
    page = ctx.new_page()
    page.goto(BASE, wait_until="load")
    page.wait_for_timeout(2500)  # 首页停留

    # 选择题库：AI 通识素养（第 2 张卡）
    page.eval_on_selector_all(".course", "(els) => els[1].click()")
    page.wait_for_timeout(900)
    page.click("#course-start")
    page.wait_for_selector("#quiz-view:not(.hide)")
    page.wait_for_timeout(700)

    bank = page.evaluate("BANKS.find(b => b.id === selected)")
    # 故意让第 2 题答错，用于演示错题重练
    for i, q in enumerate(bank["questions"]):
        correct = q["c"]
        choice = correct if i != 1 else (correct + 1) % 4
        page.query_selector_all("#answers .answer")[choice].click()
        page.wait_for_timeout(1100 if i == 1 else 550)
        page.click("#next-question")
        page.wait_for_timeout(450)

    page.wait_for_selector("#result-view:not(.hide)")
    page.wait_for_timeout(1800)
    page.mouse.wheel(0, 420)
    page.wait_for_timeout(1800)
    page.mouse.wheel(0, 320)
    page.wait_for_timeout(1200)

    # 错题重练
    page.click("#retry-wrong")
    page.wait_for_selector("#quiz-view:not(.hide)")
    page.wait_for_timeout(900)
    deck = page.evaluate("deck")
    page.query_selector_all("#answers .answer")[deck[0]["c"]].click()
    page.wait_for_timeout(1200)
    page.click("#next-question")
    page.wait_for_selector("#result-view:not(.hide)")
    page.wait_for_timeout(2200)

    ctx.close()
    browser.close()

videos = sorted(RAW.glob("*.webm"))
if not videos:
    raise SystemExit("未生成录制文件")
webm = videos[0]
out = EVID / "quizlab-demo.webm"
shutil.copyfile(webm, out)

ff = Path.home() / ".cache/ms-playwright/ffmpeg-1013/ffmpeg-linux"
mp4 = EVID / "quizlab-demo.mp4"
if ff.exists():
    r = subprocess.run(
        [str(ff), "-y", "-i", str(out), "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", "-an", str(mp4)],
        capture_output=True, text=True,
    )
    print("ffmpeg rc=", r.returncode)
    if r.returncode != 0:
        print(r.stderr[-1500:])
print("webm:", out, out.stat().st_size)
if mp4.exists():
    print("mp4:", mp4, mp4.stat().st_size)
