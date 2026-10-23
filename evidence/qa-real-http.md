# QuizLab 真实 HTTP 源端到端验收记录

- 目标地址：https://5d66d26eaa57dc.lhr.life/
- 执行时间（UTC）：2026-10-22T17:14:36.890989+00:00
- 结果：21 通过 / 0 失败
- 说明：使用 Playwright 驱动系统 Chrome，通过真实 HTTP origin 访问，localStorage 持久化可验证。

| 用例 | 结果 | 细节 |
|---|---|---|
| T01 首页加载 | ✅ 通过 | title=知测 QuizLab · 学过的知识，值得被记住; 题库=['大学英语六级', 'AI 通识素养', '计算机基础'] |
| T01b 桌面无横向溢出 | ✅ 通过 | {"sw": 1280, "cw": 1280, "w": 1280} |
| T02 切换 AI 题库 | ✅ 通过 | topic=AI 通识素养; 第 1 题 / 共 8 题 |
| T03 错选显示答案与解析 | ✅ 通过 | 解析=✦ 再记住这个知识点
大语言模型利用训练中学习到的模式，根据上下文生成序列，输出仍需核实。 |
| T04a AI 题库整轮完成 | ✅ 通过 | score=88 分, right=7, wrong=1 |
| T04b 错题清单为本轮错题 | ✅ 通过 | 错题条数=1 |
| T05 错题重练只出现本轮错题 | ✅ 通过 | 第 1 题 / 共 1 题 |
| T06 全对时错题重练禁用 | ✅ 通过 | score=100 分, disabled=True |
| T07a 首页本机统计累计 | ✅ 通过 | sessions=2, accuracy=89% |
| T07 刷新后本地记录保留 | ✅ 通过 | 刷新前 2/89% → 刷新后 2/89% |
| T08 取消清除时数据不变 | ✅ 通过 | sessions=2 |
| T08b 确认后清空 | ✅ 通过 | sessions=0 |
| T04c 英语题库 6/8=75 分 | ✅ 通过 | {"score": "75 分", "right": "6", "wrong": "2", "time": "5 秒", "wrong_items": 2} |
| T04d 错题重练题数=2 | ✅ 通过 | wrong_items=2 |
| T04e 计算机题库全对 100 分 | ✅ 通过 | {"score": "100 分", "right": "8", "wrong": "0", "time": "5 秒", "wrong_items": 0} |
| T09 键盘 1-4 作答 / Enter 下一题 | ✅ 通过 | answersGiven=1, advanced=True |
| T10 375px 无横向溢出 | ✅ 通过 | {"sw": 375, "cw": 375, "w": 375} |
| T10b 375px 完成整轮答题 | ✅ 通过 | {"score": "100 分", "right": "8", "wrong": "0", "time": "4 秒", "wrong_items": 0} |
| T10c 768px 无横向溢出 | ✅ 通过 | {"sw": 768, "cw": 768, "w": 768} |
| T11 无 JavaScript 运行错误 | ✅ 通过 | pageerrors=[] |
| T11b 无 console error | ✅ 通过 | console_errors=[] |
