# Git版本控制

## 概念

**Git** 是一个分布式版本控制系统，用于跟踪文件变化、协调多人协作和维护项目历史。与集中式版本控制（如SVN）不同，Git每个参与者都拥有完整的仓库副本，包括全部历史记录。

```
┌─────────────────────────────────────────────────────────────┐
│                     Git 分布式模型                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│   │ Developer│    │ Developer│    │ Developer│              │
│   │    A     │    │    B     │    │    C     │              │
│   └───┬──────┘    └───┬──────┘    └───┬──────┘              │
│       │                │                │                    │
│       └────────────────┼────────────────┘                    │
│                        ↓                                     │
│              ┌─────────────────────┐                         │
│              │   Remote Repository  │                         │
│              │   (GitHub/GitLab)    │                         │
│              └─────────────────────┘                         │
│                                                              │
│   每个开发者都拥有完整的本地仓库副本                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Git 核心概念

### 三种状态

Git文件在三个状态之间转换：

```
┌─────────────────────────────────────────────────────────────┐
│                    Git 文件三种状态                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐ │
│   │   Modified  │ ───→ │   Staged    │ ───→ │  Committed  │ │
│   │  (已修改)    │      │  (已暂存)    │      │  (已提交)    │ │
│   └─────────────┘      └─────────────┘      └─────────────┘ │
│         ↑                    │                    │          │
│         │                    │                    │          │
│         └────────────────────┴────────────────────┘          │
│                        │                                     │
│                 git add              git commit             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

| 状态 | 说明 | 存储位置 |
|------|------|----------|
| Modified | 文件已修改但未暂存 | 工作目录 (.git directory外) |
| Staged | 修改已加入暂存区 | .git/index |
| Committed | 已提交到本地仓库 | .git/objects |

### 四个区域

```
┌─────────────────────────────────────────────────────────────┐
│                     Git 四个区域                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   1. Working Directory (工作目录)                            │
│      - 项目的一个版本                                         │
│      - 当前看到的文件                                          │
│                                                              │
│   2. Staging Area / Index (暂存区)                          │
│      - 即将提交的文件快照                                     │
│      - 位于 .git/index                                       │
│                                                              │
│   3. Local Repository (本地仓库)                              │
│      - 提交后的历史记录                                       │
│      - 位于 .git/objects                                     │
│                                                              │
│   4. Remote Repository (远程仓库)                            │
│      - GitHub/GitLab等托管服务                               │
│      - 用于团队协作                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Git 基础命令

### 初始化与配置

```bash
# 初始化新仓库
git init

# 克隆远程仓库
git clone https://github.com/user/repo.git
git clone --depth 1 https://github.com/user/repo.git  # 浅克隆

# 配置用户信息
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 查看配置
git config --list
git config user.name  # 查看单项配置
```

### 基本操作

```bash
# 查看当前状态
git status
git status -s  # 简洁输出

# 查看差异
git diff        # 工作区 vs 暂存区
git diff --staged  # 暂存区 vs 上次提交
git diff HEAD   # 工作区 vs 仓库

# 暂存文件
git add file.txt          # 暂存单个文件
git add .                 # 暂存所有更改
git add -p                # 交互式暂存（选择部分更改）

# 提交
git commit -m "Commit message"
git commit -am "message"  # 自动暂存已跟踪文件并提交

# 查看提交历史
git log
git log --oneline         # 单行显示
git log --graph           # 图形化显示分支
git log -n 5              # 最近5条
git log --author="name"   # 按作者筛选
```

### 文件操作

```bash
# 重命名/移动文件
git mv old_name.txt new_name.txt

# 删除文件
git rm file.txt           # 从工作区和暂存区删除
git rm --cached file.txt  # 只从暂存区删除（取消跟踪）

# 恢复文件
git checkout -- file.txt  # 丢弃工作区更改
git restore file.txt      # 新版命令，效果相同
git restore --staged file.txt  # 取消暂存

# 查看文件在某个提交的内容
git show HEAD:path/to/file.txt
```

## 分支管理

### 分支基础

```bash
# 查看分支
git branch              # 本地分支
git branch -r           # 远程分支
git branch -a           # 所有分支

# 创建分支
git branch feature-x

# 切换分支
git checkout feature-x
git switch feature-x    # 新版命令

# 创建并切换
git checkout -b feature-x
git switch -c feature-x # 新版命令

# 删除分支
git branch -d feature-x   # 安全删除（已合并）
git branch -D feature-x   # 强制删除
```

### 合并分支

```bash
# 合并分支到当前分支
git merge feature-x

# 常见合并类型
# - Fast-forward: 无冲突，直接前移指针
# - 3-way merge: 有冲突，创建合并提交
```

```bash
# 解决合并冲突
# 1. 打开冲突文件，手动编辑
# 2. 删除 <<<<<<<, =======, >>>>>>> 标记
# 3. git add resolved_file.txt
# 4. git commit 完成合并
```

### 变基 (Rebase)

```bash
# 变基：将当前分支的提交在目标分支上重放
git rebase main

# 交互式变基（修改提交历史）
git rebase -i HEAD~3  # 修改最近3个提交

# 变基选项：
# pick - 保留提交
# reword - 修改提交消息
# squash - 将提交合并到上一个
# fixup - 丢弃提交消息
# drop - 删除提交
```

```bash
# 变基示例：合并多个提交
pick abc123 Fix bug
squash def456 Add tests
squash ghi789 Update docs
# 结果：一个包含三个更改的提交
```

### 贮藏 (Stash)

```bash
# 贮藏当前更改
git stash
git stash save "message"

# 查看贮藏列表
git stash list

# 应用最新贮藏
git stash apply        # 保留贮藏
git stash pop          # 应用并删除

# 应用特定贮藏
git stash apply stash@{2}

# 清空贮藏
git stash drop stash@{0}
git stash clear
```

## 远程仓库

### 远程操作

```bash
# 查看远程仓库
git remote -v

# 添加远程仓库
git remote add origin https://github.com/user/repo.git

# 重命名远程
git remote rename origin upstream

# 查看远程详细信息
git remote show origin

# 拉取但不合并
git fetch origin

# 拉取并合并
git pull origin main
git pull --rebase origin main  # 变基式拉取

# 推送
git push origin main
git push -u origin feature-x   # 设置上游分支
git push --force               # 强制推送（危险！）
```

### 跟踪关系

```bash
# 查看跟踪分支
git branch -vv

# 设置上游跟踪
git branch -u origin/feature-x
git push -u origin feature-x

# 取消跟踪
git branch --unset-upstream feature-x
```

## Git 内部原理

### 对象模型

Git使用四种对象存储所有数据：

```
┌─────────────────────────────────────────────────────────────┐
│                    Git 对象类型                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  blob - 文件内容快照                                         │
│  tree - 目录结构（包含多个blob和tree引用）                    │
│  commit - 指向tree的指针 + 元数据 + 父提交                    │
│  tag - 指向commit的命名指针                                   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ commit abc123                                      │    │
│  │   tree: def456                                    │    │
│  │   parent: 789abc                                   │    │
│  │   author: ...                                     │    │
│  │   message: "..."                                  │    │
│  └─────────────────────────────────────────────────────┘    │
│          ↓                                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ tree def456                                       │    │
│  │   100644 blob file1.txt (content)                 │    │
│  │   040000 tree subdir/ ( subtree)                  │    │
│  └─────────────────────────────────────────────────────┘    │
│          ↓                                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ blob (file1.txt content)                           │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### SHA-1 哈希

Git使用SHA-1哈希来标识对象：

```bash
# 完整SHA-1 (40字符)
git log --format="%H"

# 短哈希 (7字符)
git log --format="%h"

# SHA-1 计算
echo "hello" | git hash-object --stdin
# 输出: 8ab686eafeb1f44702738c8b0f24f2567c36da6d
```

### .git 目录结构

```
.git/
├── config          # 仓库配置
├── description     # 仓库描述
├── HEAD           # 当前分支指针
├── hooks/         # 客户端/服务端钩子
├── objects/       # 所有Git对象
│   ├── pack/      # 打包后的对象
│   └── info/      # 对象信息
├── refs/          # 分支和标签指针
│   ├── heads/     # 本地分支
│   ├── tags/      # 标签
│   └── remotes/   # 远程分支
├── index         # 暂存区
├── info/         # 额外信息
└── logs/         # 引用的历史记录
```

### 引用 (Refs)

```bash
# HEAD指针
cat .git/HEAD
# ref: refs/heads/main

# 分支指针
cat .git/refs/heads/main
# abc123def456...

# 符号引用
HEAD~1    # 上一个提交
HEAD^     # 同上
HEAD~3    # 上3个提交
```

## 高级操作

### 重置与回退

```bash
# 三种重置模式
git reset --soft HEAD~1   # 保留更改在暂存区
git reset --mixed HEAD~1  # 保留更改在工作区（默认）
git reset --hard HEAD~1   # 丢弃所有更改（危险！）

# 回退到远程状态
git reset --hard origin/main

# 反向提交（创建新提交来撤销）
git revert HEAD~1
```

### Cherry-pick

```bash
# 挑选单个提交应用到当前分支
git cherry-pick abc123

# 挑选多个提交
git cherry-pick abc123 def456

# 挑选并继续（如果有冲突）
git cherry-pick --continue
git cherry-pick --abort
```

### 交互式暂存

```bash
# 交互式暂存部分文件
git add -i
git add -p

# 选项：
# y - 暂存此区块
# n - 跳过此区块
# s - 分割成更小块
# e - 手动编辑
# q - 退出
```

### 清理与优化

```bash
# 清理未跟踪文件
git clean -n    # 预览
git clean -f     # 删除未跟踪文件
git clean -fd    # 包括目录

# 删除所有未跟踪文件（包括ignored）
git clean -fx

# 垃圾回收
git gc

# 验证仓库完整性
git fsck

# 压缩仓库
git repack -a -d
```

## 标签管理

### 创建标签

```bash
# 创建轻量标签
git tag v1.0.0

# 创建附注标签（推荐）
git tag -a v1.0.0 -m "Version 1.0.0"

# 给历史提交打标签
git tag -a v0.9.0 abc123 -m "Version 0.9.0"

# 推送标签
git push origin v1.0.0
git push origin --tags   # 推送所有标签

# 删除标签
git tag -d v1.0.0            # 本地
git push origin --delete v1.0.0  # 远程
```

## 子模块

### 子模块操作

```bash
# 添加子模块
git submodule add https://github.com/user/repo.git libs/repo

# 克隆包含子模块的仓库
git clone --recurse-submodules https://github.com/user/repo.git

# 更新子模块
git submodule update --remote libs/repo

# 初始化子模块
git submodule init

# 在子模块中工作
cd libs/repo
git checkout main
git pull
cd ../..
git add libs/repo
git commit -m "Update submodule"
```

## Git 工作流

### Git Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Git Flow 工作流                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   main ────────────────────────────────                     │
│     ↑        ↑                           ↑                  │
│     │        │                           │                  │
│     │   ┌────┴──────┐                   │                  │
│     │   │            │                   │                  │
│     └───│  release   │←──────────────────┘                  │
│         └────┬───────┘                                      │
│               ↑                                              │
│               │                                              │
│   develop ───┴───────────────────────────────────           │
│               ↑                                              │
│     ┌─────────┼─────────┐                                  │
│     ↑         ↑         ↑                                   │
│   feature/A  feature/B  feature/C                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

```bash
# Git Flow 命令
git flow init
git flow feature start feature-x
git flow feature finish feature-x
git flow release start v1.0.0
git flow release finish v1.0.0
git flow hotfix start hotfix-x
git flow hotfix finish hotfix-x
```

### GitHub Flow

适合持续部署的工作流：

```bash
# 1. 创建分支
git checkout -b feature-x

# 2. 开发并提交
git add .
git commit -m "Add feature X"

# 3. 推送并创建PR
git push -u origin feature-x
# 在GitHub上创建Pull Request

# 4. 讨论和审查

# 5. 合并到main
git checkout main
git pull origin main
git branch -d feature-x
```

## 忽略文件

### .gitignore

```gitignore
# 常见模式
*.log              # 忽略所有.log文件
node_modules/      # 忽略目录
build/             # 忽略目录
.env               # 忽略特定文件
!lib/app.js        # 强制包含（例外）

# 模式匹配
?.js               # 忽略任意单字符开头的.js
**/temp           # 匹配任意目录下的temp

# 注释
# 这是注释
```

### 全局忽略

```bash
# 设置全局忽略文件
git config --global core.excludesFile ~/.gitignore_global
```

## 高级技巧

### 搜索与查找

```bash
# 在提交历史中搜索
git log --grep="fix bug" --oneline
git log -S "function_name" --oneline  # 搜索代码变更

# 查找删除某行的提交
git log -p -S "deleted_text" --all

# 查找文件改名
git log --name-status --follow -- path
```

### 调试与检查

```bash
# 查看谁修改了某行
git blame path/to/file.txt

# 查看两个提交的差异
git diff abc123..def456

# 查看某个提交的全部文件
git show abc123 --stat

# 查找丢失的提交（reflog）
git reflog
git checkout -b recovery abc123
```

### bisect 二分查找

```bash
# 自动二分查找定位问题提交
git bisect start
git bisect bad HEAD
git bisect good v1.0.0
# Git自动checkout中间的提交
# 测试后标记
git bisect good  # 如果当前版本正常
git bisect bad   # 如果当前版本有问题
# 重复直到找到第一个bad提交
git bisect reset  # 结束
```

### 子树合并

```bash
# 添加子树
git remote add other-repo https://github.com/user/repo.git
git fetch other-repo
git read-tree --prefix=libs/repo -u other-repo/main
git pull -s subtree other-repo main
```

## 常见错误与解决

### 撤销操作

```bash
# 撤销未提交的更改
git checkout -- file.txt
git restore file.txt

# 撤销暂存
git reset HEAD file.txt
git restore --staged file.txt

# 撤销提交（创建反向提交）
git revert HEAD

# 修改最后一次提交
git commit --amend
git commit --amend --no-edit
```

### 处理冲突

```bash
# 在rebase中解决冲突
git rebase main
# 编辑冲突文件
git add .
git rebase --continue
git rebase --abort  # 放弃rebase

# 在merge中解决冲突
git merge feature-x
# 编辑冲突文件
git add .
git commit
```

### 修复远程问题

```bash
# 撤销已经push的提交
git revert abc123
git push origin main

# 删除远程分支
git push origin --delete feature-x

# 清理无效的远程跟踪分支
git remote prune origin
```

## 关系

**关键连接**：
- Git → **VCS**：版本控制是软件工程的基础设施
- 分支 → **并行开发**：分支实现多人并行开发
- 远程仓库 → **团队协作**：GitHub/GitLab是协作平台
- .gitignore → **构建系统**：与构建产物协同工作
