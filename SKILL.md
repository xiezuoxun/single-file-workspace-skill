---
name: single-file-workspace
description: Build a generic, zero-dependency single-file HTML workspace (dashboard, tracker, roster, progress board) for any team or personal use. Use when the user asks for a workbench, dashboard, tracker, kanban, check-in board, roster manager, progress board, or any "one page to organize my things". Produces one self-contained HTML file with inline CSS/JS/SVG, localStorage persistence, JSON backup, offline-first behavior, and PC/mobile responsive layout. Domain-neutral by design: no industry terms, no real names, no external services required.
---

# Single-File Workspace

把一个需求变成**一个可以直接双击打开的 HTML 文件**：数据本地持久化、断网可用、手机电脑都能用、零外部依赖。

## 适用与不适用

适用：任务清单、进度看板、成员/物品名册、打卡矩阵、目标达成、轻量记录台账、复盘汇总。

不适用：账号体系与权限后台、多人实时协同（需要服务端）、大文件/视频存储、系统通知推送、需要地图或第三方 SDK 的场景。这些都不要硬塞进单文件里。

## 工作流

### 1. 先过规模闸门

- 用户说的需求先折算成**模块数**。一次最多 3-4 个模块，这是硬上限。
- 超过 4 个：先给分期方案（本期核心 3 个 + 后续每期追加 1 个），不要一次性全量生成。
- 预估单文件超过约 60KB：**先写骨架**（HTML 结构、CSS、CONFIG、数据层、各模块占位符与统一刷新入口），再按模块分多次增量替换占位符。每补完一个模块，文件仍须可运行。
- 占位符用精确唯一串（如 `/* MODULE_TASKS */`），检查时也要精确匹配，别用会误命中常量前缀的短串。

### 2. 从模板起步

复制 `assets/workspace-template.html`，改两处即可跑起来：

1. `CONFIG` —— 标题、分组、指标、状态、字段、配色、存储前缀。
2. `seedData()` —— 3-5 条示例数据，其中 1 条必须是逾期状态，另附「清空示例」按钮。

模板已内置 4 个通用模块：今日待处理 / 进度看板 / 成员名册 / 目标与扩充。删减模块时只删对应渲染函数与导航项，不要动数据层和 `refreshAll()`。

### 3. 铁律清单（每条都必须满足）

| # | 规范 |
|---|---|
| 1 | 单文件，CSS/JS/图标/图表全内联。**绝不引用任何 CDN、外部字体、框架、图表库**。图表用手写内联 SVG，图标用 SVG path，不用 emoji 当图标。字体用系统字体栈。 |
| 2 | 数据存 localStorage，key 统一前缀 `ws_{标识}_`。附带「导出 JSON 备份」「导入恢复」两个**首屏可见**按钮；导入不设条数上限；清空需二次确认。 |
| 3 | 首屏「今天要处理」置顶：自动列出逾期、今天该做、快到期；逾期标红并给一键处理按钮；**昨天没做完的自动顺延到今天**。 |
| 4 | 首次打开必须有 3-5 条示例数据（含 1 条逾期），不能是空白页；提供「清空示例」。 |
| 5 | 移动适配：<768px 单列；按钮 ≥44×44px；输入框字号 ≥16px（否则 iOS 自动放大）；宽表横滚时 `position:sticky` 冻结首列；数字用 `type="number"`；底部留 `env(safe-area-inset-bottom)`。 |
| 6 | 汇总行/汇总卡的口径写进界面提示，且**汇总必须基于全量数据计算**，不能把当前筛选后的行相加（切换分组维度就会漏数据）。 |
| 7 | 图表与视觉：进度环、条形、关系图一律手写 SVG；同组图表固定画布尺寸与半径，不用随数据量变化的半径。 |
| 8 | 依赖注入式云同步（可选）：宿主提供 `window.HostDB` 才启用，否则静默降级纯本地；页面显示同步状态；离线操作暂存本地，恢复后补传。 |
| 9 | 函数调用链必须是 DAG：数据层 → 计算层 → 渲染层，单向；**渲染函数之间严禁互调**；所有联动走统一入口 `refreshAll()`。 |
| 10 | 交付前逐条过冒烟自检，见下节。 |

### 4. 代码架构（防递归，最容易翻车的地方）

```
数据层   load() / save() / markDirty()            只读写存储
计算层   stats() / aggregate() / filter()        纯函数，只返回数据
渲染层   renderToday() / renderBoard() / ...    只读状态，各自拼 HTML 字符串
入口     refreshAll()                           按固定顺序调用各渲染函数
交互     onXxx() → 改数据 → save() → refreshAll()
```

- 渲染函数 A 内部不许调渲染函数 B，B 也不许调 A —— 语法正确但运行时栈溢出，静态检查拦不住。
- 需要联动时，事件处理函数里改完数据统一调 `refreshAll()`。
- `DOMContentLoaded` 里固定顺序：加载数据 → 初始化状态 → 绑定事件 → `refreshAll()`。
- 输入框类交互绑 `change` 而不是 `input`：每次敲字就重建 DOM 会让输入框失焦。

### 5. 交付前冒烟自检

用 `scripts/smoke_check.py` 跑一遍，并人工确认：

1. 调用链无环（画出函数关系，确认没有 A→B→A）。
2. 初始化链路通畅，被调用的函数都已定义。
3. 所有 `getElementById` 目标在 HTML 中存在。
4. localStorage 为空时能正确填充示例数据；清空示例后不报错。
5. 日期边界：跨月、跨年、闰年不错位。
6. 事件绑定在 DOM 就绪之后。
7. 无全局变量冲突，循环内闭包变量正确捕获。
8. 本期模块数 ≤ 4；超限的已分期；超大文件已按骨架+增量写入完成。
9. 全文无外链、无真实姓名/组织/地域/凭证/内部地址。

### 6. 交付

- 交付单个 HTML 文件即可用；需要手机访问时再部署成静态网页并给链接（微信里打不开本地文件，只能给链接）。
- 提醒：页面公网可访问时不要预填任何真实隐私数据；本地文件的数据只在浏览器里，定期导出 JSON 备份。
- 手机浏览器打开 → 分享 → 添加到主屏幕，即可当 APP 用。

## 目录

- `assets/workspace-template.html` — 可运行的通用模板（改 CONFIG 即可定制）
- `references/architecture.md` — 分层、存储、云适配、备份、汇总口径
- `references/customization.md` — CONFIG 字段说明与扩展模块步骤
- `references/pitfalls.md` — 实测踩坑清单
- `scripts/smoke_check.py` — 静态扫描 + JS 语法 + 渲染桩自检
- `examples/sample-config.json` — 配置示例

## 隐私与通用性

本 skill 与模板**不含任何真实组织、地域、行业术语、人名、凭证、内部地址或业务数据**，示例均为虚构占位。若从既有页面提炼，必须先做全量脱敏：业务名词换成中性词、真实名册换成占位数据、移除硬编码的标识符与本地路径。
