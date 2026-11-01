# 上架规范：如何把一个 skill 提交到本仓库

**本文件是给 AI Agent / Agent 团队看的作业规范。** 如果你的任务是"开发一个 skill 并上架到
chinaretaildesign 的 skill 仓库"，请逐条读完再动手，最后按第 5 节的自检清单逐项打勾。

## 0. 一句话理解这个仓库

`agent-skills` 是一个**技能货架**：每个 skill 是 `skills/` 下的一个独立目录，仓库根目录的
README 是索引表。**不要把你的 skill 直接放在仓库根目录**，也不要改动别人的 skill 目录。

## 1. 目录结构（硬性）

```
skills/<skill-name>/
├── SKILL.md          # 必需。YAML frontmatter + Markdown 指令
├── scripts/          # 可选。需要确定性执行、会被反复用到的代码
├── references/       # 可选。schema / API 文档 / 领域知识，按需加载
└── assets/           # 可选。模板、图片、字体等直接用于产出的资源
```

- `<skill-name>` 只能用**小写字母、数字、连字符**（如 `pdf-table-extract`），不得含空格或中文。
- **渐进式披露**：SKILL.md 保持精简（建议 < 5k 词），细节一律放 `references/`，避免撑爆上下文。
- 脚本要能独立运行、自带 `--help`，并在 SKILL.md 里写清调用示例。

## 2. SKILL.md 的 frontmatter 规范（硬性）

```yaml
---
name: <skill-name>
description: <第三人称，说明这个 skill 做什么、在什么场景下使用。这一行决定它会不会被触发。>
agent_created: true
---
```

`description` 是**最关键的字段**——AI 靠它判断何时调用。必须写清两件事：

1. 这个 skill 具体做什么
2. 用户会说什么样的话来触发它（把典型触发语句写进去）

反例（太模糊，不会触发）：`description: 处理文档`
正例：`description: 从 PDF 中提取表格并导出为 Excel。当用户说「把 PDF 里的表格转成 Excel」、
「提取这个 PDF 的表格数据」或需要处理扫描件表格时使用。`

`agent_created: true` 必须保留，否则后续无法通过 skill 管理功能修改或删除。
**从 GitHub 等外部引入的第三方 skill 通常没有这个字段，上架前必须补上**——
自检脚本会把它当 error 拦住。

## 3. 三条红线（违反直接拒收）

1. **不得包含任何密钥、令牌、密码、内网地址、个人身份信息。** 需要凭证时写成读环境变量
   （如 `os.environ["API_KEY"]`），并在 SKILL.md 里说明如何获取。
2. **不得引入未声明的外部依赖。** 若需要 Python 包，必须提供 `requirements.txt`（**锁定版本**），
   并在 SKILL.md 的「依赖」一节写清安装命令。
3. **不得有破坏性行为的默认动作。** 删除、覆盖、外发（邮件/推送/公开）类操作必须默认
   `dry-run` 或先列清单等待确认。

## 4. 交付流程

先判断你属于哪种情况：

### 4A. 与仓库所有者在同一台机器上（SSH 密钥共享）

```bash
git clone git@github.com:chinaretaildesign/agent-skills.git
cd agent-skills
# 1. 开发：在 skills/<skill-name>/ 下写你的东西
# 2. 自检（必做）：
python scripts/validate_skill.py skills/<skill-name>
# 3. 更新根目录 README.md 的索引表（新增一行）
# 4. 本地提交，但【不要 push】：
git add -A
git -c user.name="chinaretaildesign" -c user.email="sammy1505196888@126.com" \
    commit -m "Add skill: <skill-name>"
# 5. 把改动清单（新增/修改了哪些文件）列给仓库所有者，等他明确确认后再 push
git push origin master
```

**第 5 步的等待确认是硬性的。** 未经确认不得 push——这是仓库所有者的既定规矩。

### 4B. 在别的机器上，或是外部贡献者（fork + PR）

```bash
# 1. Fork 本仓库，clone 你的 fork
# 2. 建分支：git checkout -b skill/<skill-name>
# 3. 开发 + 自检：python scripts/validate_skill.py skills/<skill-name>
# 4. 提交并推到你的 fork：git push origin skill/<skill-name>
# 5. 开 Pull Request，标题写 [Skill] <skill-name>，正文照抄下方模板
```

PR 正文模板：

```
## 这个 skill 做什么
<一到三句话>

## 典型触发语句
- 「……」
- 「……」

## 依赖
- Python 包：<包名==版本> 或 无
- 外部命令 / 运行时：<如 Node 18+> 或 无
- 需要的凭证 / 环境变量：<如 API_KEY> 或 无

## 自检清单
- [ ] python scripts/validate_skill.py 全部通过
- [ ] SKILL.md frontmatter 含 name / description / agent_created: true
- [ ] 无密钥、令牌、内网地址等敏感信息
- [ ] 依赖已锁定版本，且有安装说明
- [ ] 破坏性操作默认 dry-run 或先列清单确认
- [ ] 已更新根目录 README.md 索引表
```

## 5. 提交前自检清单（逐项确认）

- [ ] 目录是 `skills/<小写连字符名>/`，没有放在仓库根目录
- [ ] `SKILL.md` 存在，frontmatter 含 `name` / `description` / `agent_created: true`
- [ ] `description` 写清了「做什么」+「什么场景下触发」，且是第三人称
- [ ] `python scripts/validate_skill.py skills/<skill-name>` 全部通过
- [ ] SKILL.md 精简，细节已下沉到 `references/`
- [ ] 脚本可独立运行，有 `--help`，SKILL.md 里有调用示例
- [ ] 无敏感信息；依赖已锁版本并写明安装方式
- [ ] 破坏性操作默认不执行
- [ ] 已更新根目录 README.md 索引表
- [ ] **（4A 情形）已本地 commit，并把清单交给所有者等待 push 授权**

## 6. 迭代与下架

- 改已有的 skill：改完走同样流程，**生成新版本不要直接覆盖**原文件（保留 v1 便于回退）。
- 下架：不要直接删目录。在 PR 或提交说明里写明原因，由所有者确认后移除，并同步删掉 README 索引行。
