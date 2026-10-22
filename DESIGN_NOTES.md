# 知测 QuizLab｜V2 视觉规范（Apple × Anthropic 风格取向）

## 设计定位
“温和、专注、有书卷气的数字学习工具”。保留独立视觉，参考 Apple 的秩序与克制、Anthropic 的暖色调与编辑式排版，不复用品牌资产。

## 已完成的变化
- 由紫色渐变通用模板，升级为暖白（#f8f7f2）/森林绿（#2f493c）/陶土橙（#ac6a4b）。
- 中文衬线大标题；大面积留白、细分割线、小字英文说明构建层次。
- 右侧为纯 CSS + HTML 的纸质测验卡，脱离“浮动 UI 卡片 + Emoji”的 AI 模板观感。
- 题库使用三张不同的色块卡片，Aa/✳/{ } 字符用于视觉区分。
- 答题、解析、成绩、错题页全部与首页使用统一的配色、边框与按钮语言。
- 完全保留原版 24 道题、3 题库、localStorage、键盘操作、错题重练。

## 设计禁区
不引入激进动效、炫彩渐变、浮夸 Emoji、玻璃拟态噪声、重动画或复杂图标库。不要照搬 Apple / Anthropic 商标、布局截图或文案。

## 验证记录
Playwright Chromium 本地内容测试：3 题库渲染、错题重练、逐题评分、结果总数正确、390px 无横向溢出、键盘 1-4/Enter、JS 无页面错误。浏览器测试使用 `set_content`，其运行环境不具备可验证的持久化 origin，故刷新后存储验证留待真实 HTTP 部署环境。图片：`evidence/v2-desktop-premium.png`, `v2-mobile-premium.png`, `v2-quiz-premium.png`, `v2-result-premium.png`。
