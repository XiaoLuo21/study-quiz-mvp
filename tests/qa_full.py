"""QuizLab 真实 HTTP 源端到端验收脚本（Playwright + 系统 Chrome）。

用法：.venv/bin/python tests/qa_full.py [http://127.0.0.1:8080/]
输出：evidence/qa-real-http.json + evidence/qa-real-http.md，并在 evidence/ 下截图。
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080/"
ROOT = Path(__file__).resolve().parent.parent
EVID = ROOT / "evidence"
EVID.mkdir(exist_ok=True)

results = []
console_errors = []
page_errors = []


def record(case, ok, detail):
    results.append({"case": case, "ok": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + case + " — " + detail)


def no_hscroll(pg, width):
    return pg.evaluate(
        "() => ({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, w: window.innerWidth})"
    ), pg.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1")


def start_bank(pg, bank_index):
    pg.goto(BASE, wait_until="load")
    pg.eval_on_selector_all(
        ".course", "(els, i) => els[i].click()", bank_index
    )
    pg.click("#course-start")
    pg.wait_for_selector("#quiz-view:not(.hide)")
    return pg.evaluate("BANKS")[bank_index]


def answer(pg, bank, q_index, choice):
    """点击第 q_index 题的指定选项；返回 true/false 是否答对。"""
    q = bank["questions"][q_index]
    btns = pg.query_selector_all("#answers .answer")
    assert len(btns) == 4, "选项数量不是 4"
    btns[choice].click()
    correct = choice == q["c"]
    # 校验不可重复作答
    assert pg.evaluate("document.querySelectorAll('#answers button:not([disabled])').length") == 0, "答题后仍可再次点击"
    classes = pg.eval_on_selector_all("#answers .answer", "els => els.map(e => e.className)")
    exp_visible = pg.eval_on_selector("#explanation", "e => !e.classList.contains('hide')")
    exp_text = pg.inner_text("#explanation")
    assert exp_visible and "再记住" in exp_text if not correct else "回答正确" in exp_text
    assert "correct" in classes[q["c"]], "正确选项未标绿"
    if not correct:
        assert "wrong" in classes[choice], "错选未标红"
    return correct


def finish(pg, bank, picks):
    """picks: 每题的选项下标。返回结果页数据。"""
    n = len(picks)
    for i, choice in enumerate(picks):
        answer(pg, bank, i, choice)
        if i < n - 1:
            pg.click("#next-question")
            pg.wait_for_function(f"document.querySelector('#q-number').textContent.includes('第 {i+2} 题')")
        else:
            pg.click("#next-question")
    pg.wait_for_selector("#result-view:not(.hide)")
    score = pg.inner_text("#score").strip()
    data = {
        "score": score,
        "right": pg.inner_text("#right-num").strip(),
        "wrong": pg.inner_text("#wrong-num").strip(),
        "time": pg.inner_text("#time-num").strip(),
        "wrong_items": pg.eval_on_selector_all(".wrongitem", "els => els.length"),
    }
    return data


def select_indices(bank, correct_flags):
    """correct_flags 每项 True=选对，False=选错（错选自动选非正确项）。"""
    out = []
    for q, ok in zip(bank["questions"], correct_flags):
        out.append(q["c"] if ok else (q["c"] + 1) % 4)
    return out


with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/usr/bin/google-chrome",
        headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage"],
    )
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="zh-CN")
    pg = ctx.new_page()
    pg.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: page_errors.append(str(e)))

    # T01 首页
    pg.goto(BASE, wait_until="load")
    title = pg.title()
    h1 = pg.inner_text("h1")
    courses = pg.eval_on_selector_all(".course h3", "els => els.map(e => e.textContent)")
    record("T01 首页加载", "知测 QuizLab" in title and len(courses) == 3,
           f"title={title}; 题库={courses}")
    pg.screenshot(path=str(EVID / "01-home-desktop.png"), full_page=False)

    # 横向溢出检查（桌面）
    dims, ok = no_hscroll(pg, 1280)
    record("T01b 桌面无横向溢出", ok, json.dumps(dims))

    # T02 切换题库 → AI
    bank_ai = start_bank(pg, 1)
    qnum = pg.inner_text("#q-number")
    record("T02 切换 AI 题库", "AI 通识素养" in pg.inner_text("#quiz-topic") and "共 8 题" in qnum,
           f"topic={pg.inner_text('#quiz-topic')}; {qnum}")

    # T03 第 1 题错选
    q0 = bank_ai["questions"][0]
    wrong_choice = (q0["c"] + 1) % 4
    correct = answer(pg, bank_ai, 0, wrong_choice)
    after = pg.eval_on_selector_all("#answers .answer", "els => els.map(e => e.className)")
    record("T03 错选显示答案与解析", (not correct) and any("wrong" in c for c in after) and any("correct" in c for c in after),
           f"解析={pg.inner_text('#explanation')[:50]}")
    pg.screenshot(path=str(EVID / "02-question.png"), full_page=False)

    # 继续完成 8 题：其余全对 → 7 对 1 错 = 88 分（四舍五入）
    picks = [wrong_choice] + [q["c"] for q in bank_ai["questions"][1:]]
    for i in range(1, 8):
        pg.click("#next-question")
        pg.wait_for_function(f"document.querySelector('#q-number').textContent.includes('第 {i+1} 题')")
        answer(pg, bank_ai, i, picks[i])
    pg.click("#next-question")
    pg.wait_for_selector("#result-view:not(.hide)")
    score = pg.inner_text("#score").strip()
    right = pg.inner_text("#right-num").strip()
    wrong = pg.inner_text("#wrong-num").strip()
    record("T04a AI 题库整轮完成", right == "7" and wrong == "1" and score == "88 分",
           f"score={score}, right={right}, wrong={wrong}")
    record("T04b 错题清单为本轮错题", pg.eval_on_selector_all(".wrongitem", "els=>els.length") == 1,
           "错题条数=1")
    pg.screenshot(path=str(EVID / "03-result.png"), full_page=False)

    # T05 错题重练仅 1 题
    pg.click("#retry-wrong")
    pg.wait_for_selector("#quiz-view:not(.hide)")
    record("T05 错题重练只出现本轮错题", "共 1 题" in pg.inner_text("#q-number") and "错题重练" in pg.inner_text("#quiz-topic"),
           pg.inner_text("#q-number"))

    # 答对并完成 → 100 分、错题重练禁用
    q_wrong = pg.evaluate("deck[0]")
    answer(pg, {"questions": [q_wrong]}, 0, q_wrong["c"])
    pg.click("#next-question")
    pg.wait_for_selector("#result-view:not(.hide)")
    retry_disabled = pg.is_disabled("#retry-wrong")
    record("T06 全对时错题重练禁用", pg.inner_text("#score").strip() == "100 分" and retry_disabled,
           f"score={pg.inner_text('#score').strip()}, disabled={retry_disabled}")
    pg.screenshot(path=str(EVID / "03b-result-perfect.png"), full_page=False)

    # 统计已累计 2 次
    pg.click("#go-home")
    sessions = pg.inner_text("#sessions")
    acc = pg.inner_text("#accuracy")
    record("T07a 首页本机统计累计", sessions == "2", f"sessions={sessions}, accuracy={acc}")

    # T07 刷新后保留
    pg.reload(wait_until="load")
    sessions2 = pg.inner_text("#sessions")
    acc2 = pg.inner_text("#accuracy")
    record("T07 刷新后本地记录保留", sessions2 == "2" and acc2 == acc,
           f"刷新前 {sessions}/{acc} → 刷新后 {sessions2}/{acc2}")

    # T08 清除取消
    pg.once("dialog", lambda d: d.dismiss())
    pg.click("#reset-data")
    record("T08 取消清除时数据不变", pg.inner_text("#sessions") == "2", f"sessions={pg.inner_text('#sessions')}")
    pg.once("dialog", lambda d: d.accept())
    pg.click("#reset-data")
    record("T08b 确认后清空", pg.inner_text("#sessions") == "0", f"sessions={pg.inner_text('#sessions')}")

    # 英语题库完整 8 题，6 对 2 错 → 75 分，错题 2
    bank_en = start_bank(pg, 0)
    flags = [True, True, False, True, True, False, True, True]
    picks = select_indices(bank_en, flags)
    res = finish(pg, bank_en, picks)
    record("T04c 英语题库 6/8=75 分", res["score"] == "75 分" and res["right"] == "6" and res["wrong"] == "2",
           json.dumps(res, ensure_ascii=False))
    record("T04d 错题重练题数=2", res["wrong_items"] == 2, f"wrong_items={res['wrong_items']}")
    pg.screenshot(path=str(EVID / "03c-result-75.png"), full_page=False)

    # 计算机题库完整 8 题全对 → 100
    bank_cs = start_bank(pg, 2)
    res2 = finish(pg, bank_cs, [q["c"] for q in bank_cs["questions"]])
    record("T04e 计算机题库全对 100 分", res2["score"] == "100 分" and res2["wrong_items"] == 0,
           json.dumps(res2, ensure_ascii=False))

    # 键盘操作：1-4 作答 + Enter 下一题
    pg.goto(BASE, wait_until="load")
    pg.click("#course-start")
    pg.keyboard.press("1")
    answered = pg.evaluate("answersGiven.length")
    pg.keyboard.press("Enter")
    advanced = "第 2 题" in pg.inner_text("#q-number")
    record("T09 键盘 1-4 作答 / Enter 下一题", answered == 1 and advanced,
           f"answersGiven={answered}, advanced={advanced}")
    pg.screenshot(path=str(EVID / "02b-keyboard.png"), full_page=False)

    # 移动端 375×812 完整一轮
    mctx = browser.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=2,
                               is_mobile=True, has_touch=True, locale="zh-CN")
    mp = mctx.new_page()
    mp.on("pageerror", lambda e: page_errors.append("mobile: " + str(e)))
    mp.goto(BASE, wait_until="load")
    dims_m, ok_m = no_hscroll(mp, 375)
    record("T10 375px 无横向溢出", ok_m, json.dumps(dims_m))
    mp.screenshot(path=str(EVID / "04-mobile.png"), full_page=False)
    bank_m = start_bank(mp, 1)
    res_m = finish(mp, bank_m, [q["c"] for q in bank_m["questions"]])
    record("T10b 375px 完成整轮答题", res_m["score"] == "100 分", json.dumps(res_m, ensure_ascii=False))
    mp.screenshot(path=str(EVID / "04b-mobile-result.png"), full_page=False)

    # 平板 768
    tctx = browser.new_context(viewport={"width": 768, "height": 1024}, locale="zh-CN")
    tp = tctx.new_page()
    tp.goto(BASE, wait_until="load")
    dims_t, ok_t = no_hscroll(tp, 768)
    record("T10c 768px 无横向溢出", ok_t, json.dumps(dims_t))

    record("T11 无 JavaScript 运行错误", len(page_errors) == 0, f"pageerrors={page_errors}")
    record("T11b 无 console error", len(console_errors) == 0, f"console_errors={console_errors}")

    browser.close()

summary = {
    "base_url": BASE,
    "time_utc": datetime.now(timezone.utc).isoformat(),
    "domain_origin": BASE.split("/")[2],
    "passed": sum(1 for r in results if r["ok"]),
    "failed": sum(1 for r in results if not r["ok"]),
    "results": results,
    "console_errors": console_errors,
    "page_errors": page_errors,
}
(EVID / "qa-real-http.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
md = ["# QuizLab 真实 HTTP 源端到端验收记录", "",
      f"- 目标地址：{BASE}",
      f"- 执行时间（UTC）：{summary['time_utc']}",
      f"- 结果：{summary['passed']} 通过 / {summary['failed']} 失败",
      "- 说明：使用 Playwright 驱动系统 Chrome，通过真实 HTTP origin 访问，localStorage 持久化可验证。", "",
      "| 用例 | 结果 | 细节 |", "|---|---|---|"]
for r in results:
    md.append(f"| {r['case']} | {'✅ 通过' if r['ok'] else '❌ 失败'} | {r['detail']} |")
(EVID / "qa-real-http.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(f"\n{summary['passed']} passed, {summary['failed']} failed")
sys.exit(0 if summary["failed"] == 0 else 1)
