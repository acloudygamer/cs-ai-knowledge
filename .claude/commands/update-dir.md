# update-dir

扫描语言目录，忠实更新 PROJECT_STATUS.md 的目录结构部分。

## 执行步骤

### 第一步：扫描语言目录

运行以下命令，忠实记录每个语言目录下的实际子目录：

```bash
for dir in 0-计算机基础 1-数据结构与算法 2-Python 3-C++ 4-Java 5-JavaScript 6-Go; do
  echo "### $dir/"
  echo ""
  echo "| 子目录 | 说明 |"
  echo "|--------|------|"
  for subdir in "$dir"/*/; do
    subdir=${subdir%/}
    echo "| ${subdir#$dir/}/ | |"
  done
  echo ""
done
```

### 第二步：扫描项目脚本与资源目录结构

```bash
echo "### 项目结构"; echo ""; echo '```'; ls -la .claude/agents/ | tail -n +2 | awk '{print $NF}' | grep -v '^\.\.?$'; echo "---"; ls -la prompts/ | tail -n +2 | awk '{print $NF}' | grep -v '^\.\.?$'; echo "---"; ls -la scripts/ | tail -n +2 | awk '{print $NF}' | grep -v '^\.\.?$'; echo "---"; ls scripts/tasks/ | tail -n +2 | awk '{print $NF}' | grep -v '^\.\.?$'; echo '```'
```

### 第三步：更新 PROJECT_STATUS.md

将第一步和第二步的输出，对应替换 PROJECT_STATUS.md 中以下章节：

1. `## 目录结构` 下方的语言主表 — 保持不变（目录名和 Agent 映射关系固定）
2. `### 0-计算机基础/` 到 `### 6-Go/` 的所有子目录表 — 替换为第一步输出
3. `### 项目结构` — 替换为第二步输出

### 第四步：提交变更

```bash
git add PROJECT_STATUS.md && git commit -m "chore: 更新 PROJECT_STATUS.md 目录结构"
```

## 注意事项

- 忠实记录实际存在的子目录，不做任何修改或合并
- 编号重复的子目录（如 2-Python 有两个 04-）如实保留
- 不存在的章节不生成，保持原样
