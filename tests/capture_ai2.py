import os, subprocess, time, json
from playwright.sync_api import sync_playwright

ANCHORS = [
 ("01", "你现在是本项目的全权开发负责人"),
 ("02", "T03 错选显示答案与解析"),
 ("03", "21 passed, 0 failed"),
 ("04", "galleries-adaptive-signed-transition"),
]
JS_FIND = """
(anchor) => {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let best=null, n;
  while (n = walker.nextNode()) {
    if (n.textContent && n.textContent.includes(anchor)) {
      const el = n.parentElement;
      if (!best || el.getBoundingClientRect().width < best.getBoundingClientRect().width) best = el;
    }
  }
  if(!best) return null;
  const r = best.getBoundingClientRect();
  const socks=[];
  let p=best.parentElement;
  while(p){
    const cs=getComputedStyle(p);
    if(p.scrollHeight>p.clientHeight+20 && /(auto|scroll)/.test(cs.overflowY))
      socks.push({cls:p.className, top:p.getBoundingClientRect().top, st:p.scrollTop, sh:p.scrollHeight, ch:p.clientHeight});
    p=p.parentElement;
  }
  return {text:best.textContent.slice(0,80), y:r.top, x:r.left, h:r.height, socks};
}
"""
JS_SCROLL = """
([anchor]) => {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let best=null, n;
  while (n = walker.nextNode()) {
    if (n.textContent && n.textContent.includes(anchor)) {
      const el=n.parentElement; if(!best||el.getBoundingClientRect().width<best.getBoundingClientRect().width) best=el;
    }
  }
  if(!best) return 'notfound';
  let p=best.parentElement;
  while(p){
    const cs=getComputedStyle(p);
    if(p.scrollHeight>p.clientHeight+20 && /(auto|scroll)/.test(cs.overflowY)){
      const er=best.getBoundingClientRect(), pr=p.getBoundingClientRect();
      p.scrollTop += (er.top - pr.top) - 140;
      return 'scrolled ' + p.className.slice(0,40) + ' -> ' + p.scrollTop;
    }
    p=p.parentElement;
  }
  window.scrollBy(0, best.getBoundingClientRect().top - 200);
  return 'window';
}
"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1500,"height":940})
    pg.goto("http://127.0.0.1:3081/", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(5000)
    try:
        pg.get_by_text("Running", exact=True).first.click(timeout=30000)
    except Exception as e:
        print("click fail", e)
        pg.screenshot(path="/tmp/gui-first.png")
        raise SystemExit(1)
    pg.wait_for_timeout(5000)
    for name, anchor in ANCHORS:
        info = pg.evaluate(JS_FIND, anchor)
        print(name, json.dumps(info, ensure_ascii=False)[:600])
        if not info:
            continue
        print(" scroll:", pg.evaluate(JS_SCROLL, [anchor]))
        pg.wait_for_timeout(1200)
        pg.screenshot(path=f"evidence/ai-5-{name}.png")
        subprocess.run(["convert", f"evidence/ai-5-{name}.png", "-crop", "1200x760+260+120", "+repage", f"/tmp/ai-5-{name}-crop.png"])
        print("  OCR:", subprocess.run(["tesseract", f"/tmp/ai-5-{name}-crop.png", "-", "-l", "chi_sim+eng"], capture_output=True, text=True).stdout.replace("\n"," ")[:160])
    b.close()
