"""可选的浏览器功能冒烟测试。运行：python tests/smoke_test.py
需要本机安装 playwright + chromium。测试代码没有连接公网、不会制造真实用户数据。
优先使用本地 HTTP；如受策略限制则用 set_content 验证 JavaScript 交互。
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
from datetime import datetime
ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'index.html'
EVID=ROOT/'evidence'
EVID.mkdir(exist_ok=True)

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else None,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1280,'height':800},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    # 不暗示公网链接成功；这是本地 HTML 注入的交互测试。
    page.set_content(HTML.read_text(encoding='utf-8'),wait_until='load')
    assert page.locator('.course').count()==3
    page.screenshot(path=str(EVID/'local-home-desktop.png'),full_page=True)
    page.locator('#course-start').click()
    corrects=page.evaluate('BANKS.find(x=>x.id==="english").questions.map(q=>q.c)')
    for i,c in enumerate(corrects):
        chosen=c if i<6 else (c+1)%4
        page.locator('.answer').nth(chosen).click()
        assert page.locator('.answer.correct').count()==1
        assert page.locator('#next-question').is_enabled()
        if i==0: page.screenshot(path=str(EVID/'local-question-desktop.png'),full_page=True)
        page.locator('#next-question').click()
    assert page.locator('#score').inner_text().split()[0]=='75'
    assert page.locator('#right-num').inner_text()=='6'
    assert page.locator('#wrong-num').inner_text()=='2'
    page.screenshot(path=str(EVID/'local-result-desktop.png'),full_page=True)
    page.locator('#retry-wrong').click()
    assert '共 2 题' in page.locator('#q-number').inner_text()
    for c in corrects[-2:]:
        page.locator('.answer').nth(c).click();page.locator('#next-question').click()
    assert page.locator('#score').inner_text().split()[0]=='100'
    assert page.locator('#retry-wrong').is_disabled()
    page.locator('#result-back').click()
    assert page.locator('#sessions').inner_text()=='2'
    page.locator('.course').nth(1).click()
    page.locator('#course-start').click()
    assert 'AI 通识' in page.locator('#quiz-topic').inner_text()
    page.keyboard.press('1');page.keyboard.press('Enter')
    assert '第 2 题' in page.locator('#q-number').inner_text()
    page.locator('#quiz-back').click()
    page.set_viewport_size({'width':375,'height':812})
    page.screenshot(path=str(EVID/'local-home-mobile.png'),full_page=True)
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'), '手机端出现横向溢出'
    page.locator('.course').nth(2).click();page.locator('#course-start').click()
    comp_correct=page.evaluate('BANKS.find(x=>x.id==="computer").questions.map(q=>q.c)')
    for c in comp_correct:
        page.locator('.answer').nth(c).click();page.locator('#next-question').click()
    assert page.locator('#score').inner_text().split()[0]=='100'
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    assert errors==[],errors
    print('PASS: 3 个题库切换；6/8=75 分；错题重练=2 道；全对=100 分；键盘；375 px 移动端；无 JS 错误')
    print('注：此脚本的 set_content 不代表公网部署测试，也不覆盖刷新后 localStorage 持久化。')
    browser.close()
