# single-file-workspace-skill

一个可复用的 **Skill + 零依赖单文件 HTML 模板**，用来快速搭出「一个页面管好一件事」的团队 / 个人工作台：进度看板、任务清单、名册、目标达成、跟进台账。

生成的产物是**一个 HTML 文件**：CSS、JS、图标、图表全部内联，双击即用、断网可用、手机电脑自适应，不需要构建、不需要服务器、不需要任何第三方库。

## 为什么做成单文件

AI 生成的页面常引用 CDN 图表库或字体，用户把 HTML 另存到本地后这些资源 404，功能直接全废。这个模板把所有依赖收进文件内：进度环、柱状图、关系图都是手写内联 SVG；数据存 localStorage；云同步做成可选适配器，宿主不提供就纯离线。

## 快速开始

1. 复制 `assets/workspace-template.html`。
2. 改 `CONFIG`：标题、分组、指标、阶段、字段、存储主键、配色。
3. 改 `seedData()`：换成你的示例数据（保留 3-5 条、其中 1 条逾期）。
4. 双击打开即可用。需要手机访问时，把这一个文件部署到任意静态托管，拿链接打开 → 分享 → 添加到主屏幕。

定制细节见 `references/customization.md`，架构与口径见 `references/architecture.md`，踩坑清单见 `references/pitfalls.md`。

## 目录

```
SKILL.md                          Skill 指令：工作流、铁律、自检清单
assets/workspace-template.html    可运行的通用模板（改 CONFIG 即可定制）
references/architecture.md       分层 / 存储 / 云适配 / 汇总口径 / 响应式
references/customization.md      CONFIG 字段表与扩展模块步骤
references/pitfalls.md           实测踩坑清单
scripts/smoke_check.py           静态扫描 + JS 语法 + 渲染桩自检
examples/sample-config.json      配置示例
```

## 内置能力

- 首屏「今天要处理」置顶：逾期标红、一键处理、未完成的自动顺延到今天
- 进度看板：按分组 / 负责人切换、指标实际完成与覆盖率、**全量口径汇总行**、内联 SVG 柱状图
- 成员名册：行内编辑、CSV / JSON **追加导入（只新增不覆盖）**、CSV 模板下载与导出
- 目标与扩充：手填目标、环形进度、固定尺寸关系星链图、通栏汇总卡、跟进明细
- 数据安全：首屏导出 JSON / 导入恢复、清空与删除二次确认、同步状态指示、云端失败静默降级本地
- 移动适配：抽屉导航、宽表横滚冻结首列、16px 输入框、44px 按钮、底部安全区

## 架构约束

函数调用链必须是 DAG：数据层 → 计算层 → 渲染层，渲染函数之间严禁互调，所有联动走统一的 `refreshAll()`。一次最多 3-4 个模块，超出先分期。详见 `SKILL.md`。

## 自检

```bash
python scripts/smoke_check.py
python scripts/smoke_check.py --html /path/to/your-workspace.html --node /path/to/node
python scripts/smoke_check.py --deny-file /path/to/forbidden-terms.txt
```

检查项：结构标记、零外链、通用风险模式（绝对路径 / 内网 IP / 疑似凭证）、渲染函数无环、`node --check`、渲染桩（汇总行数量、全量口径、追加导入不覆盖、空数据不崩）。`--deny-file` 可传入自定义禁用词表，词表本身不入库。

## 通用性与隐私声明

本仓库**不含任何真实组织、地域、行业术语、人名、编号、凭证、内部地址或业务数据**。分组、指标、成员、负责人均为中性占位；示例值全部虚构；模板不绑定任何具体平台或服务。

从既有页面提炼时，务必先做全量脱敏：业务名词换成中性词、真实名册换成占位数据、移除硬编码的标识符与本地路径、清理注释里的内部信息，再提交到公开仓库。公开链接任何人拿到都能打开，不要在页面里预填真实隐私数据。

## License

MIT — 见 `LICENSE`。
