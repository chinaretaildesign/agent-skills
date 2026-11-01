# 交接文件：授权另一个 Agent 团队上架 skill

> 这份文件给**仓库所有者（黄老师）**和**接活的 Agent 团队**一起看。
> 团队先看第 1 节确认自己的身份，再按对应路径走；第 4 节是给所有者的授权操作手册。

## 仓库信息

| 项 | 值 |
| --- | --- |
| 仓库 | https://github.com/chinaretaildesign/agent-skills |
| clone（SSH，有写权限） | `git@github.com:chinaretaildesign/agent-skills.git` |
| clone（HTTPS，只读） | `https://github.com/chinaretaildesign/agent-skills.git` |
| 上架规范 | 仓库内 `CONTRIBUTING.md`（动手前必读） |
| 任务简报模板 | 仓库内 `TEAM_PROMPT.md`（复制粘贴给团队用） |
| 自检命令 | `python scripts/validate_skill.py skills/<skill-name>` |
| 默认分支 | `master` |

## 1. 团队先确认：你属于哪种情况

### 情形 A：你跑在仓库所有者的同一台电脑上

SSH 密钥（`~/.ssh/id_ed25519`）就在本机，你**天生有推送权限**，无需任何授权步骤。
直接按 `CONTRIBUTING.md` 第 4A 节流程干活：

+ clone → 在 `skills/<skill-name>/` 开发 → 自检全绿 → 更新 README 索引表
+ **本地 commit 后停下，把改动清单交给所有者，等他明确说"推"才能 push**

### 情形 B：你在另一台机器上，需要写权限（直接推 master）

需要所有者先给你授权，见第 3 节（推荐 **Deploy Key** 方式，只限本仓库）。
拿到授权后，流程同情形 A。

### 情形 C：你在另一台机器上，不需要写权限（走 PR）

无需任何授权：

1. Fork 仓库到你自己的账号
2. 建分支 `skill/<skill-name>`，开发 + 自检
3. 推到你的 fork，开 Pull Request，标题 `[Skill] <skill-name>`
4. PR 正文照抄 `CONTRIBUTING.md` 第 4B 节模板，等所有者审核合并

## 2. 无论哪种情形，铁律相同

+ 提交前 `python scripts/validate_skill.py skills/<skill-name>` 必须**全绿**
+ skill 放 `skills/<小写连字符名>/`，SKILL.md frontmatter 必须含
  `name` / `description` / `agent_created: true`
+ 禁止提交密钥、令牌、内网地址（自检脚本会拦）
+ **未经所有者确认，不得把代码推到 master**（情形 A/B）；PR 合并权只在所有者手里（情形 C）
+ 迭代已有 skill 生成新版本，不直接覆盖

## 3. 给所有者：怎么给另一台机器授权（情形 B）

推荐用 **Deploy Key**——只授权这一个仓库，泄露了影响面也小：

1. 让对方在那台机器上生成密钥，把**公钥**发给你（整行，`ssh-ed25519 AAAA...` 开头）：
   ```bash
   ssh-keygen -t ed25519 -C "agent-team-<机器标识>" -f ~/.ssh/id_ed25519 -N ""
   cat ~/.ssh/id_ed25519.pub
   ```
2. 打开 https://github.com/chinaretaildesign/agent-skills/settings/keys/new
3. Title 填 `agent-team-<机器标识>`；Key 粘贴公钥；
   **勾选 Allow write access**（不勾就只能读，推不了）
4. 告诉对方"已授权"，对方用 SSH 地址 clone 即可
5. 收回授权：同一页面删掉那把 key 即可，对方立即失去写权限

> 三种授权方式对比：
> | 方式 | 权限范围 | 适合 |
> | --- | --- | --- |
> | **Deploy Key（推荐）** | 仅这一个仓库，可读写可收回 | 固定的协作机器 |
> | 个人 SSH Key | 该 GitHub 账号全部仓库 | 只有所有者自己的机器 |
> | Fork + PR | 无写权限，审核后合并 | 外部贡献者、不可信环境 |

## 4. 所有者的验收动作（团队说"做完了"之后）

1. 看团队交来的自检输出，确认 validate_skill.py **全绿、退出码 0**
2. 自己抽查：
   ```bash
   python scripts/validate_skill.py skills/<skill-name>
   git log --oneline -5          # 确认只多了预期提交
   git diff HEAD~1 --stat        # 确认改动范围没有越界
   ```
3. 确认无误后回复"可以推"，团队执行 `git push`（或你自己推）
4. push 后检查 README 索引表已更新、线上 `git ls-remote` 有新提交
