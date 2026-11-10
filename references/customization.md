# 定制指南

模板里**只有两处需要改**：`CONFIG` 和 `seedData()`。其余代码是通用骨架，尽量别动。

## CONFIG 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `title` | string | 页面标题、侧栏品牌、手机顶栏标题 |
| `subtitle` | string | 备用副标题，可写进描述文案 |
| `storageKey` | string | localStorage 主键。**换场景必须改名**，否则同源页面会互相覆盖 |
| `groups` | `{id,name}[]` | 一级分组。增删改只改这里，看板 / 目标卡 / 明细下拉自动跟着变 |
| `metrics` | `{id,name,defaultTarget}[]` | 要跟踪的指标列。数量建议 3-6 个，太多在手机上要横滚 |
| `states` | string[] | 状态枚举（预留给扩展模块） |
| `stages` | string[] | 扩充明细的阶段下拉 |
| `activeStages` | string[] | 计入「跟进中」的阶段，也是置顶待跟进的筛选条件 |
| `rosterFields` | string[] | 名册 CSV 表头，需与 `renderRoster()` 的列顺序一致 |
| `accent` | string | 主色，同步改 `:root` 里 `--accent` / `--accent-d` |

改 `groups` 时记得同步 `seedData()` 里的 `targets` / `goals` 键，否则目标输入框会显示为空（不会报错，只是没默认值）。

## seedData()

返回完整初始状态。约定：

```js
{
  version, demo,
  owners:  [{ id, name, group }],
  members: [{ id, group, owner, code, name, note }],
  progress: { 'YYYY-MM-DD': { memberId: { metricId: number } } },
  targets:  { groupId: { metricId: number } },
  tasks:    [{ id, title, due, done }],
  goals:    { groupId: number },
  headcount:{ groupId: number },
  pipeline: [{ id, group, name, stage, createdAt }]
}
```

要求：

- 预置 **3-5 条**示例数据，其中 **1 条逾期**（`due` 早于今天且 `done:false`），让首屏「今天要处理」立刻有内容。
- 示例值全部用占位名（「示例成员 01」这种），不要放真实姓名、真实编号或真实业务数值。
- `demo:true` 用于识别示例状态；「清空示例数据」按钮负责清掉它们。

## 配色

改 `:root` 里的 CSS 变量即可，其余样式都引用变量：

```
--bg / --surface / --surface2   背景层次
--line / --line2                边框
--txt / --txt2                  文字
--accent / --accent-d           主色与深主色
--ok / --warn / --bad / --info  语义色
```

国内习惯：支出/负面用红、收入/正面用绿；金额符号用 `¥`；日期用 `YYYY-MM-DD`。

## 增删指标 / 分组

1. 改 `CONFIG.metrics` 或 `CONFIG.groups`。
2. 改 `seedData()` 里对应的 `progress` / `targets` 示例值与默认目标。
3. 看板表头、汇总行、柱状图都由 `CONFIG.metrics` 循环生成，**不用改渲染代码**。
4. 若新增自定义字段，记得在 `normalize()` 的字段列表里补上，保证旧数据平滑升级。

## 追加一个模块

一次只加 1 个，不丢已有数据：

1. 在 `CONFIG` 里加该模块的配置项，在 `seedData()` / `normalize()` 里加对应存储字段（用新键名，不动旧键）。
2. 写纯计算函数放在计算层，只返回数据。
3. 写 `renderXxx()` 放在渲染层，只读状态、只拼字符串，**不调用其它渲染函数**。
4. 在 `refreshAll()` 的分支里挂上它（或加一个导航项）。
5. 在 `handleAct()` / `handleInput()` 里接交互：改数据 → `save()` → `refreshAll()`。
6. 跑一遍 `scripts/smoke_check.py`。

## 追加导入（不覆盖）

`applyRosterImport()` 的语义是「只追加」：

- 去重键 `code || name`；
- 已存在的记录直接 `skipped++`，**不修改任何字段**；
- 只 `push` 新记录，已有进度、目标、备注全部不受影响。

如果业务需要「更新已有记录」，不要改成整体替换，正确做法是 `merge`：以新数据的基础字段为准，保留旧记录的扩展字段，并保留本地独有的记录。整体替换会在每次定时导入时把用户后来填的字段全部冲掉。

## 部署

- 本地双击 HTML 即可用；数据只在当前浏览器。
- 需要手机访问时，把这一个文件部署到任意静态托管，拿到链接即可；不要给 HTML 文件本身（聊天软件里打不开）。
- 公网页面不要预填真实隐私数据；链接是公开可访问的。
- 手机浏览器打开 → 分享 → 添加到主屏幕，即可当 APP 用。

## 云同步（可选）

宿主注入 `window.HostDB`（契约见 `architecture.md`）即启用；不注入自动离线。不要把任何服务端地址、标识或凭证硬编码进模板。
