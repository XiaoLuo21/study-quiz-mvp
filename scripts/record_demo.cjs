// Record real interactions with the public deployment. No application state is injected.
const { chromium } = require('C:/Users/HP/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const out = path.join(root, 'output/playwright/quizlab-demo-20261023');
const ev = path.join(root, 'evidence/video-20261023');
const url = 'https://xiaoluo21.github.io/study-quiz-mvp/';
const preflight = process.argv.includes('--preflight');
fs.mkdirSync(out, { recursive: true });
fs.mkdirSync(ev, { recursive: true });

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/HP/AppData/Local/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-win64/chrome-headless-shell.exe' });
  const context = await browser.newContext({ viewport: { width: 1600, height: 800 }, deviceScaleFactor: 1, locale: 'zh-CN', ...(preflight ? {} : { recordVideo: { dir: out, size: { width: 1600, height: 800 } } }) });
  const videoEpoch = Date.now();
  await context.addInitScript(() => {
    // A presentation cursor only; no quiz data, scores, or storage are altered.
    window.addEventListener('DOMContentLoaded', () => {
      const cursor = document.createElement('div');
      cursor.setAttribute('aria-hidden','true');
      cursor.style.cssText = 'position:fixed;left:-50px;top:-50px;width:14px;height:14px;border:2px solid #fff;border-radius:50%;background:#355a47;box-shadow:0 0 0 4px #355a4735;z-index:2147483647;pointer-events:none;transform:translate(-50%,-50%)';
      document.documentElement.append(cursor);
      window.addEventListener('mousemove', e => {cursor.style.left=e.clientX+'px';cursor.style.top=e.clientY+'px'});
      window.addEventListener('mousedown', () => {cursor.style.boxShadow='0 0 0 12px #b16c473d';cursor.style.background='#b16c47'});
      window.addEventListener('mouseup', () => {cursor.style.boxShadow='0 0 0 4px #355a4735';cursor.style.background='#355a47'});
    });
  });
  const page = await context.newPage();
  const log = { url, startedAt: new Date().toISOString(), preflight, browser: browser.version(), viewport: { width:1600, height:800 }, actions: [], errors: [] };
  page.on('pageerror', e => log.errors.push(String(e)));
  const response = await page.goto(url, { waitUntil: 'networkidle' });
  assert.equal(response.status(), 200);
  log.httpStatus = response.status();
  await page.evaluate(() => document.fonts.ready);
  log.liveTitle = await page.title();
  const started = Date.now();
  log.clipStartOffsetEstimate = (started-videoEpoch)/1000;
  log.presentationOverlay = 'Small mouse pointer only. Application logic and data are unmodified.';
  const at = async (sec, action, fn) => {
    if (!preflight) await page.waitForTimeout(Math.max(0, sec * 1000 - (Date.now() - started)));
    await fn();
    log.actions.push({ targetSecond: sec, actualSecond: +( (Date.now() - started)/1000 ).toFixed(3), action });
    console.log(JSON.stringify(log.actions.at(-1)));
  };
  const shot = async name => page.screenshot({ path: path.join(ev, `${preflight ? 'preflight-' : ''}${name}.png`) });
  const frameQuestion = () => page.evaluate(() => {
    const heading = document.querySelector('#question-title');
    window.scrollTo({top: window.scrollY + heading.getBoundingClientRect().top - 125, behavior:'smooth'});
  });
  const click = async locator => {
    const box = await locator.boundingBox();
    if (box) await page.mouse.move(box.x + box.width/2, box.y + box.height/2, { steps: 12 });
    await locator.click();
  };
  await shot('01-home');
  await at(12, 'Scroll from home to the three course cards', () => click(page.locator('#hero-start')));
  await page.waitForTimeout(preflight ? 30 : 700);
  await shot('02-courses');
  await at(20, 'Select AI general knowledge', () => click(page.getByRole('button', { name: /AI 通识素养/ })));
  await at(24.5, 'Start the selected eight-question quiz', () => click(page.locator('#course-start')));
  assert.match(await page.locator('#question-title').innerText(), /大语言模型/);
  await at(28.3, 'Q1: answer correctly with B', () => click(page.getByRole('button', { name: '选项 B：基于上下文预测并生成语言', exact: true })));
  assert.match(await page.locator('#explanation').innerText(), /回答正确/);
  await at(29.3, 'Frame the complete question and feedback below the fixed navigation', frameQuestion);
  await page.waitForTimeout(preflight ? 30 : 500);
  await shot('03-correct-feedback');
  await at(33, 'Advance to Q2', () => click(page.locator('#next-question')));
  assert.match(await page.locator('#question-title').innerText(), /提示词/);
  await at(35.5, 'Q2: deliberately choose wrong answer A', () => click(page.getByRole('button', { name: '选项 A：随便写一句“弄一下”', exact: true })));
  assert.equal(await page.locator('.answer.wrong').count(), 1);
  assert.equal(await page.locator('.answer.correct').count(), 1);
  await at(36.5, 'Frame the wrong answer, correct answer, and explanation together', frameQuestion);
  await page.waitForTimeout(preflight ? 30 : 500);
  await shot('04-wrong-feedback');
  const answers = [0,1,1,2,2,1];
  for(let i=0;i<answers.length;i++) {
    await at(44.4 + i*0.95, `Advance to Q${i+3}`, () => click(page.locator('#next-question')));
    await at(44.8 + i*0.95, `Q${i+3}: select correct visible option`, () => click(page.locator('#answers .answer').nth(answers[i])));
  }
  await at(50.2, 'Submit the eight real answers and show the score report', () => click(page.locator('#next-question')));
  assert.match(await page.locator('#score').innerText(), /88/);
  assert.equal(await page.locator('#right-num').innerText(), '7');
  assert.equal(await page.locator('#wrong-num').innerText(), '1');
  log.firstReport = await page.locator('#result-view').innerText();
  await shot('05-report-88');
  await at(53.5, 'Show the current-round wrong-question review and retry control', () => page.locator('#retry-wrong').scrollIntoViewIfNeeded());
  await at(57.5, 'Retry only the one wrong question', () => click(page.locator('#retry-wrong')));
  assert.match(await page.locator('#q-number').innerText(), /共 1 题/);
  await at(59.5, 'Answer the retry correctly with C', () => click(page.getByRole('button', { name: '选项 C：明确目标、输入和约束', exact: true })));
  await shot('06-retry-one-question');
  await at(62.5, 'Show the retry score report', () => click(page.locator('#next-question')));
  assert.match(await page.locator('#score').innerText(), /100/);
  assert.equal(await page.locator('#retry-wrong').isDisabled(), true);
  log.retryReport = await page.locator('#result-view').innerText();
  await shot('07-retry-report-100');
  await at(67, 'Return to the course collection', () => click(page.locator('#result-back')));
  await at(68, 'Scroll to this device learning record', () => page.locator('.analytics').scrollIntoViewIfNeeded());
  assert.equal(await page.locator('#sessions').innerText(), '2');
  assert.equal(await page.locator('#accuracy').innerText(), '89%');
  log.storageBeforeReload = await page.evaluate(() => localStorage.getItem('quizlab.study.v1'));
  await shot('08-device-record');
  await at(73, 'Reload the public deployment to demonstrate persisted learning records', async () => {
    await page.reload({waitUntil:'networkidle'});
    await page.locator('.analytics').scrollIntoViewIfNeeded();
  });
  log.storageAfterReload = await page.evaluate(() => localStorage.getItem('quizlab.study.v1'));
  assert.equal(log.storageBeforeReload, log.storageAfterReload);
  await shot('09-persisted-after-refresh');
  await at(78.5, 'Return to the home hero for the closing statement', () => page.evaluate(() => window.scrollTo({top:0,behavior:'smooth'})));
  await at(85, 'Finish the recording', async () => {});
  log.actualInteractionDuration = +( (Date.now()-started)/1000 ).toFixed(3);
  log.finishedAt = new Date().toISOString();
  const video = page.video();
  await context.close();
  if (video) { log.rawVideo = path.join(out, 'public-live-raw.webm'); await video.saveAs(log.rawVideo); }
  await browser.close();
  fs.writeFileSync(path.join(ev, preflight ? 'preflight.json' : 'recording.json'), JSON.stringify(log,null,2));
  console.log(JSON.stringify({success:true, preflight, errors:log.errors, rawVideo:log.rawVideo}));
})().catch(e=>{console.error(e); process.exit(1)});
