# Git版本控制

> **版本基准**: universal

## 定义

Git是分布式版本控制系统，通过内容寻址存储和快照模型记录文件变更历史。核心抽象是**内容哈希寻址**：每个对象（blob/tree/commit）由其内容的 SHA-1 哈希唯一标识，内容不变则对象不变，这保证了版本历史的不可篡改性。

**归约内核**：Git 的本质是**内容寻址的分布式文件系统**。所有数据（文件内容、目录结构、提交记录）都存储为对象，通过 SHA-1 哈希引用。这使得任何两个相同内容的对象在所有克隆中是共享的，无论它们在何时何地创建。

## 数学模型

### 分支合并复杂度

Git 分支合并有三种模式：

| 合并类型 | 时间复杂度 | 空间复杂度 | 说明 |
|----------|------------|------------|------|
| Fast-forward | $O(1)$ | $O(1)$ | 指针移动，无实际合并 |
| 3-way merge | $O(n)$ | $O(n)$ | 比较三个提交 |
| 递归 3-way merge | $O(n)$ | $O(n)$ | 处理分叉历史 |

其中 $n$ 是需比较的文件数。Fast-forward 发生于合并分支与当前分支无分叉时，直接移动指针即可。

### SHA-1 哈希空间

SHA-1 输出 160 位（20 字节），哈希空间大小：

$$
|\text{space}| = 2^{160}
$$

碰撞概率在实践中可忽略：

$$
P(\text{collision after } k \text{ objects}) \approx \frac{k(k-1)}{2^{161}}
$$

对于 $k = 10^9$ 个对象（大量），碰撞概率约为 $10^{-31}$。

### 版本图结构

Git 仓库是**有向无环图（DAG）**：
- 节点：commit 对象
- 边：parent 指针
- 根节点：无 parent 的提交（初始提交）
- HEAD：指向当前分支最新提交的指针

**DAG 的数学性质**：设 $C$ 是提交集合，$parent: C \to C^k$ 是 parent 指针函数。Git 的历史是 $parent$ 函数生成的偏序关系。

## 数据流

<pre>
工作目录                          暂存区                          本地仓库                          远程仓库
    │                               │                               │                               │
    │─── 修改文件 ─────────────────►│                               │                               │
    │      (状态: Modified)         │                               │                               │
    │                               │─── git add ─────────────────►│                               │
    │                               │      (状态: Staged)           │                               │
    │                               │                               │                               │
    │                               │─── git commit ─────────────►│                               │
    │                               │      (状态: Committed)        │                               │
    │                               │                               │                               │
    │                               │                               │─── git push ────────────────►│
    │                               │                               │◄─── 远程更新 ───────────────│
</pre>

**数据形态变换链路**：

1. `工作目录文件（工作副本）` → `git add` → `暂存区快照（blob 对象）`
2. `暂存区快照` → `git commit` → `本地仓库提交（commit 对象 + tree 对象）`
3. `本地仓库提交` → `git push` → `远程仓库 refs 更新`
4. `git clone/fetch` → `远程 refs + 对象下载` → `本地仓库`
5. `git checkout` → `仓库对象` → `工作目录文件`

## 机制

### 对象不可变的约束价值

Git 对象的不可变性是**历史可信赖的根基**。一旦 commit 对象创建，其内容（tree、parent、author、message）永不改变。

约束表述：SHA-1 = Hash(content)，内容不变则哈希不变，历史篡改必然产生新节点，而非覆盖原对象。

违反此约束（强制推送修改后的历史）会导致：
- 协作者的工作基线被破坏
- 本地分支与远程分支分叉
- 丢失的提交成为"悬空对象（dangling objects）"

### 分支轻量的实现原理

Git 分支只是指向 commit 的 40 字节指针（文件内容是 SHA-1 哈希的十六进制表示）。创建分支：

```bash
# 创建 refs/heads/feature 分支指针，指向当前 HEAD 所在的 commit
git branch feature
```

此操作：
- 不拷贝任何文件
- 不存储差异
- 时间复杂度 $O(1)$

### 分布式对等的协作模型

Git 的分布式模型中，每个克隆都是完整仓库：
- 所有历史对象（commits、trees、blobs）都存在于每个克隆中
- 没有"中心服务器"的概念（除约定外）
- 协作通过 push/pull 交换对象完成

这消除了单点故障：中央服务器宕机时，任何克隆都可恢复完整历史。

### 分支策略的适用场景

| 策略 | 分支模型 | 优点 | 缺点 | 适用场景 |
|------|----------|------|------|----------|
| GitHub Flow | 主干 + 功能分支 | 简单 | 不适合多版本并行 | 持续部署 |
| Git Flow | 主干 + 开发 + 特性 + 发布 + 热修复 | 多版本支持 | 复杂 | 正式发布周期 |
| Trunk-based | 单主干 + 特性开关 | 最简 | 需要成熟 CI/CD | 大型团队 |

### Rebase vs Merge 的本质差异

| 操作 | 结果 | 历史 | 适用场景 |
|------|------|------|----------|
| Merge | 产生合并提交，保留分叉历史 | 真实但复杂 | 合并他人的工作 |
| Rebase | 重写提交，应用线性历史 | 干净但失真 | 整理本地提交 |

Rebase 重写历史提交意味着提交 SHA-1 改变。**黄金法则**：不要 rebase 已经推送的提交。

### Git 对象模型的形式化

| 对象类型 | 内容 | SHA-1 计算内容 |
|----------|------|---------------|
| blob | 文件内容 | content |
| tree | 目录结构 | tree_entries (name, mode, sha) |
| commit | 快照 + metadata | tree + parent + author + message |
| tag | 对 commit 的引用 | tagger + message + object |

对象通过内容哈希寻址保证了引用完整性。

## 参考存根

```bash
# 基本 Git 操作
git add .
git commit -m "update"
git push origin main

# 分支操作
git branch feature
git checkout feature
git merge feature

# Rebase 示例
git checkout feature
git rebase main

# 查看历史
git log --oneline --graph
git diff HEAD~3..HEAD
```

```bash
# Git 对象查看
git cat-file -t <sha>  # 对象类型
git cat-file -p <sha>  # 对象内容
git ls-tree <sha>      # tree 对象内容

# 引用查看
git show-ref          # 所有引用
git rev-parse HEAD    # HEAD 的 SHA
```
