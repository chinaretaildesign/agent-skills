# 给另一个 Agent 团队的任务简报（直接复制粘贴给他们）

> 使用方法：把下面「=== 任务开始 ===」到「=== 任务结束 ===」之间的内容整段复制，
> 粘贴到那个 WorkBuddy 任务/团队对话框里，把尖括号里的占位符替换成实际内容即可。

=== 任务开始 ===

## 你的任务

开发一个 skill，并上架到我的技能仓库 `chinaretaildesign/agent-skills`。

我要的 skill 是：**<一句话描述，例如：把口语化的 UI 效果描述翻译成准确的设计语言>**
它需要能在用户说「<典型触发语句1>」「<典型触发语句2>」这类话时被自动触发。

## 第一步：先读规范，不要凭自己的理解写

```bash
git clone git@github.com:chinaretaildesign/agent-skills.git
cd agent-skills
cat CONTRIBUTING.md
```

**完整读一遍 CONTRIBUTING.md 再动手。** 里面规定了目录结构、SKILL.md 的 frontmatter
写法、三条红线、交付流程。你的产出必须符合它，否则会被拒收。

## 硬性要求（摘要）

+ 目录必须是 `skills/<小写连字符名>/`，**不要**放在仓库根目录
+ `SKILL.md` 的 frontmatter 必须含 `name` / `description` / `agent_created: true`
+ `description` 要写清「做什么」+「什么场景下触发」，这是决定它能不能被自动触发的关键
+ 提交前必须跑自检，且**全部通过**：
  `python scripts/validate_skill.py skills/<skill-name>`
+ 不得包含密钥、令牌、内网地址；需要凭证时必须写成读环境变量
+ 依赖必须锁定版本并提供安装说明
+ 删除、覆盖、外发类操作默认 dry-run 或先列清单等我确认

## 交付规矩（最重要）

1. 开发完成 + 自检全绿 + 更新 README.md 索引表后，**本地 commit，但不要 push**
2. 把改动清单（新增/修改了哪些文件、skill 用途、触发语句、依赖）列给我
3. **等我明确回复确认后，才执行 push**

未经确认直接 push 到 master 视为违规。这是仓库所有者的既定规矩，请务必遵守。

## 完成后这样汇报

```
skill 名称：<name>
用途：<一到三句>
触发语句：
  - 「……」
依赖：<包名==版本> 或 无
自检结果：<贴 validate_skill.py 的输出>
改动文件清单：
  - skills/<name>/SKILL.md
  - ...
本地 commit：<commit hash>
待你确认后我再 push
```

=== 任务结束 ===

---

## 如果那个团队在别的机器上（没有 SSH 权限）

把上面 clone 命令换成 HTTPS，并改用 fork + PR 流程：

```bash
git clone https://github.com/chinaretaildesign/agent-skills.git
# Fork 后建分支 skill/<name>，开发 + 自检，推到自己的 fork，再开 Pull Request
# PR 标题：[Skill] <skill-name>
# PR 正文：照抄 CONTRIBUTING.md 第 4B 节的模板
```
