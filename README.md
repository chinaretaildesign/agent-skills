# agent-skills

黄老师的 Agent 技能货架：每个 skill 一个目录，统一存放、统一校验、可一键安装。

> 配套仓库：[skill-finder](https://github.com/chinaretaildesign/skill-finder)——
> 一个用来**搜索**现成 skill 的 skill。本仓库则用来**存放**自己产出的 skill。

## 安装某个 skill

```bash
git clone https://github.com/chinaretaildesign/agent-skills.git
cp -r agent-skills/skills/<skill-name> ~/.workbuddy/skills/     # 用户级，所有项目可用
# 或
cp -r agent-skills/skills/<skill-name> <工作区>/.workbuddy/skills/   # 项目级
```

装完重启一次会话让它被识别。

## 技能索引

| Skill | 用途 | 触发示例 | 依赖 |
| --- | --- | --- | --- |
| [skill-finder](skills/skill-finder/) | 到 GitHub 等市场搜寻符合需求的现成 skill，评估后推荐安装 | 「帮我找一个能读取抖音视频内容的 skill」 | Python 3.10+；无需凭证（设 `GITHUB_TOKEN` 可提高限额） |

## 我要上架一个新的 skill

**如果你是 AI Agent / Agent 团队，请完整阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 再动手。**
里面写清了目录结构、SKILL.md frontmatter 规范、三条红线、两种交付流程（同机直推 /
fork + PR）和提交前自检清单。

最短路径：

```bash
git clone git@github.com:chinaretaildesign/agent-skills.git
cd agent-skills
mkdir -p skills/<skill-name>
# 写 SKILL.md 及可选资源
python scripts/validate_skill.py skills/<skill-name>   # 必须全绿
# 更新本文件上方的索引表，然后本地 commit
```

## 交付规矩（重要）

- 同机直推的情形：**先本地 commit，把改动清单交给仓库所有者确认，确认后才 push**。
  未经确认不得 push 到 master。
- 外部贡献者：走 fork + Pull Request，由所有者审核后合并。
- 迭代已有 skill 时生成新版本，**不要直接覆盖**原文件，便于回退。

## 目录结构

```
agent-skills/
├── README.md              索引 + 安装说明
├── CONTRIBUTING.md        上架规范（Agent 必读）
├── scripts/
│   └── validate_skill.py  一键自检（提交前必跑）
└── skills/
    └── <skill-name>/      每个 skill 一个目录
        ├── SKILL.md
        ├── scripts/
        ├── references/
        └── assets/
```

## 许可

MIT
