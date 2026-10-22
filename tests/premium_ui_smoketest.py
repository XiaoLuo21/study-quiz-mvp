from pathlib import Path
from playwright.sync_api import sync_playwright
p=Path(__file__).resolve().parents[1]/"index.html"
with sync_playwright() as pw:
    b=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1440,'height':900},device_scale_factor=1)
    page=ctx.new_page()
    errors=[]
    page.on('pageerror', lambda e:errors.append(str(e)))
    page.set_content(p.read_text(encoding="utf-8"))
    assert page.locator('.course').count()==3
    page.screenshot(path=str(p.parent/'evidence'/'v2-desktop-premium.png'),full_page=True)
    page.locator('.course').nth(1).click()
    page.locator('#course-start').click()
    assert 'AI' in page.locator('#quiz-topic').inner_text()
    page.screenshot(path=str(p.parent/'evidence'/'v2-quiz-premium.png'),full_page=True)
    for i in range(8):
        page.locator('.answer').first.click()
        assert page.locator('.answer.correct').count()==1
        assert page.locator('#explanation').is_visible()
        page.locator('#next-question').click()
    assert page.locator('#result-view').is_visible()
    right=int(page.locator('#right-num').inner_text())
    wrong=int(page.locator('#wrong-num').inner_text())
    assert right+wrong==8
    page.screenshot(path=str(p.parent/'evidence'/'v2-result-premium.png'),full_page=True)
    page.locator('#retry-wrong').click()
    assert f'共 {wrong} 题' in page.locator('#q-number').inner_text()
    page.locator('#quiz-back').click()
    assert page.locator('#sessions').inner_text()=='1'
    # about:blank set_content does not provide a reliable persistent storage origin.
    # Keep persistence for live HTTP deployment verification.
    page.locator('.course').nth(2).click()
    page.locator('#course-start').click()
    page.keyboard.press('1')
    assert not page.locator('#next-question').is_disabled()
    page.keyboard.press('Enter')
    assert '第 2 题' in page.locator('#q-number').inner_text()
    page.locator('#quiz-back').click()
    page.set_viewport_size({'width':390,'height':844})
    page.screenshot(path=str(p.parent/'evidence'/'v2-mobile-premium.png'),full_page=True)
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), 'horizontal overflow'
    page.locator('.course').nth(0).click()
    page.locator('#course-start').click()
    for i in range(8):
        page.locator('.answer').nth(1).click()
        page.locator('#next-question').click()
    assert page.locator('#result-view').is_visible()
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), 'result overflow'
    assert not errors, errors
    print('PASS: 3 courses, selection, submit, score, wrong retry, session stats, keyboard, responsive 390px, console')
    b.close()
