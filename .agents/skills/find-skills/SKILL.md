---
name: find-skills
description: Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used when the user is looking for functionality that might exist as an installable skill.
---

# Find Skills

从开放 agent skills 生态发现并安装技能。注册表与排行榜：https://skills.sh/ （Vercel Labs 维护）；配套 CLI：`npx skills`（npm 包 `skills`）。

## 核心命令

- `npx skills find [query] [--owner <org>]`——按关键词搜索；`--owner` 限定 GitHub 组织
- `npx skills add <owner/repo> [--skill <名>] [-g] [-a <agent>] [-y]`——安装；`-g` 装到用户级，`-a` 指定 agent（kimi-code-cli 等项目级路径为 `.agents/skills/`）
- `npx skills use <source>`——不安装，生成 prompt 直接试用
- `npx skills list` / `remove` / `update`——管理已安装技能
- `npx skills init <name>`——创建自己的技能骨架

命令语义以 `npx skills --help` 与 vercel-labs/skills 仓库为准——生态变化快，本文件是指针不是教程。

## 质量验证（推荐前必做）

不要仅凭搜索结果就向用户推荐。逐条核：

1. **来源**：一方组织仓库（anthropics、vercel-labs、microsoft、google 等）> 排行榜高安装量 > 未知作者。
2. **安装量**：来自 CLI 遥测，只当相对流行度信号（有"只用此 CLI 的用户"的选择偏差）；绝对数字会过时，不要写进文档。
3. **安装即引入第三方代码**：SKILL.md 会被 agent 读取执行，安装前通读全文是底线。

## 获取途径的优先级

1. 一方官方仓库——策展过，质量下限最高
2. skills.sh 排行榜——真实使用流行度
3. GitHub 直接搜 `path:SKILL.md`——长尾覆盖，无质量信号，必须人工审
4. 自己写（用 skill-creator）——私有事实类技能（如本仓库 gfm-math）全网搜不到，价值最耐久

## 备注

- CLI 默认开启匿名遥测，`DISABLE_TELEMETRY=1` 关闭。
- 找不到合适技能时：直接用自己的通用能力完成任务；若是高频私有流程，建议用户自建技能。
