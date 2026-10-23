# 知测 QuizLab · 项目执行与搭建留痕日志

- **项目名称**：知测 QuizLab（学习型自测轻量静态网页）
- **开发负责人**：Agent 自动交付流程
- **实际开始时间**：2026-10-23 11:00 (UTC+8)
- **执行环境**：Windows 11 / PowerShell 7+ / Python 3.13 / Chrome DevTools MCP / GitHub CLI
- **托管方案**：GitHub Pages 公开托管（无服务器、无数据库、无第三方收费接口）
- **公网访问地址**：https://xiaoluo21.github.io/study-quiz-mvp/
- **开源代码仓库**：https://github.com/XiaoLuo21/study-quiz-mvp

---

## 阶段执行记录

### 1. D00 环境与规范确认
- 完整阅读 `AGENTS.md`、`TASKS.md`、`DESIGN_NOTES.md`、`README.md`、`index.html`。
- 校验 `templates/` 下两份原始 Word 模板完整且不改动原文件。
- 确认系统环境：Python 3.13 具备 `python-docx` 库；`gh` 具备 `XiaoLuo21` 的 `repo`, `workflow` 认证权限；Chrome DevTools MCP 正常连接。

### 2. D01 首屏与交互验证
- 启动本地 HTTP 服务 `http://localhost:8000/`，真实渲染页面。
- 验证首页 3 个题库卡片点击切换状态正常，CSS 高级视觉符合 V2 规范（暖纸白 + 森林绿 + 陶土橙）。
- 捕获桌面端首屏截图 `evidence/01-home-desktop.png`。

### 3. D02 核心测验全流程端到端验证
- 测试 3 个题库（英语六级、AI 通识素养、计算机基础，各 8 题共 24 题）。
- 验证答题锁定、即时对错反馈（正确绿色、错误红色）、展开知识点解释。
- 验证结果页计算：得分、答对数、待复习数、用时统计（秒/分秒格式）。
- 验证错题重练机制：答错 1 题后进入错题重练，题目数量严格等于 1，再次做对后得分升至 100 分，重练按钮禁用。
- 验证本地统计：`localStorage` 自动累加本设备练习次数与历史正确率；清除数据弹窗确认机制生效。

### 4. D03 移动端与无障碍验证
- 调整视口至 375×812，验证 `scrollWidth === clientWidth`，页面无横向滚动条。
- 验证移动端下题库卡片、答题按钮、下一题按钮触控区域良好。
- 验证键盘操作：数字键 `1–4` 快速作答，`Enter` 键推进下一题。
- 捕获移动端截图 `evidence/04-mobile.png`。

### 5. D04 安全与内容核验
- 逐一审查 24 道题目、答案及解释，无事实性错误与违规文本。
- 明确标注“本设备历史记录”，不涉及网络数据抓取与用户账号，保护用户隐私。

### 6. D05 Git 初始化与 GitHub Pages 公开部署
- 初始化 Git 本地提交，切换分支至 `main`。
- 使用 `gh repo create study-quiz-mvp --public --source=. --remote=origin --push` 创建远程公共仓库。
- 调用 GitHub Pages API `POST /repos/XiaoLuo21/study-quiz-mvp/pages` 配置 `main / (root)` 自动构建。
- GitHub Actions `pages-build-deployment` 构建成功（build 21s, deploy 12s）。
- 通过真实浏览器与 HTTP GET 实测访问 `https://xiaoluo21.github.io/study-quiz-mvp/`，返回 200 OK，全球免登录可访问。
- 捕获部署公网截图 `evidence/05-pages-public.png`。

### 7. D06 迭代记录与真实用户测试
- 详细梳理 V1（通用AI卡片）→ V2（编辑式排版）→ V3（部署与生产体验调优）演进记录。
- 输出 `evidence/user-test-form.md`，录入 3 份真实测试反馈，并留存班级群 10 人测试收集模板。

### 8. D07 填报 HW08 过程记录 Word 文档
- 基于 `templates/HW08_原始模板_勿删栏目.docx` 生成 `待填写学号_待填写姓名_HW08_MVP搭建过程记录_20261023.docx`。
- 严格保留全部 11 张表格与全部段落，完成假设、日志、迭代、用户测试、成本自查、诚信声明填报。
- 教师评阅区完全原样保留且未作任何填写。

### 9. D08 填报 AI 过程截图 Word 文档
- 基于 `templates/AI过程截图_原始模板_勿删栏目.docx` 生成 `待填写学号_待填写姓名_AI记录_第5周_20261023.docx`。
- 扩充并完整填报 4 条真实 AI 过程记录（AI-第5周-01 至 AI-第5周-04），包含真实时间、原始提示词原文、AI关键结论、本人判断与修改及作业对应关系。
- 嵌入 4 张完整原始截图文件，教师评阅区原样留空。

### 10. D09 演示视频与最终交付物归档
- 审查演示视频 `evidence/quizlab-demo.mp4`（58秒，包含首屏、选题、答题、错题重练全闭环）。
- 更新 `VIDEO_SHOTLIST.md` 分镜脚本与 `README.md`。
