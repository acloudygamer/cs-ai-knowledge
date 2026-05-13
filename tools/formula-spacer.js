#!/usr/bin/env node
/**
 * 公式两端空格填充脚本
 *
 * 遍历所有 .md 文件，确保 $...$ 和 $$...$$ 公式两端恰好有一个空格。
 * 规则：
 *   - 公式前必须恰好有一个空格
 *   - 公式后必须恰好有一个空格
 *
 * 用法：node formula-spacer.js [目录]
 */

const fs = require('fs');
const path = require('path');

// 处理行内公式 $...$
function processInlineFormula(line) {
  // 匹配 $...$，支持转义 \$
  const regex = /(?<!\\)\$(?!\$)((?:[^$\\]|\\.)+?)(?<!\\)\$/g;
  let result = '';
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(line)) !== null) {
    const fullMatch = match[0]; // 如 "$a + b$"
    const start = match.index;
    const end = start + fullMatch.length - 1;

    // 公式前面的部分
    const before = line.substring(lastIndex, start);
    // 公式后面的部分
    const after = line.substring(end + 1);

    // 确保前面恰好有一个空格
    let newBefore = before;
    if (before.length === 0) {
      newBefore = ' ';
    } else if (before[before.length - 1] !== ' ') {
      newBefore = before + ' ';
    }
    // 如果最后一个字符是空格但前面还有空格（多余），保留一个
    // 否则 newBefore 已经处理好了

    // 确保后面恰好有一个空格
    let newAfter = after;
    if (after.length === 0) {
      newAfter = ' ';
    } else if (after[0] !== ' ') {
      newAfter = ' ' + after;
    }

    result += newBefore + fullMatch + newAfter;
    lastIndex = end + 1;
  }

  result += line.substring(lastIndex);
  return result;
}

// 处理整行（$$...$$ 块公式）
function processBlockFormula(line) {
  // 匹配 $$...$$
  const regex = /\$\$((?:[^$\\]|\\.)+?)\$\$/g;
  let result = line;
  let match;
  let offset = 0;

  while ((match = regex.exec(line)) !== null) {
    const fullMatch = match[0];
    const start = match.index;
    const end = start + fullMatch.length - 1;

    const before = line.substring(0, start);
    const after = line.substring(end + 1);

    // 确保前面恰好有一个空格
    let newBefore = before;
    if (before.length === 0) {
      newBefore = ' ';
    } else if (before[before.length - 1] !== ' ') {
      newBefore = before + ' ';
    }

    // 确保后面恰好有一个空格
    let newAfter = after;
    if (after.length === 0) {
      newAfter = ' ';
    } else if (after[0] !== ' ') {
      newAfter = ' ' + after;
    }

    const newLine = newBefore + fullMatch + newAfter;
    result = result.substring(0, start + offset) + newLine + result.substring(end + 1 + offset);
    offset += (newLine.length - fullMatch.length);
    line = result;
  }
  return result;
}

// 遍历目录处理所有 .md 文件
function walkDir(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walkDir(fullPath);
    } else if (entry.isFile() && entry.name.endsWith('.md')) {
      processFile(fullPath);
    }
  }
}

// 处理单个文件
function processFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  let modified = false;
  const newLines = lines.map(line => {
    const processed = processBlockFormula(processInlineFormula(line));
    if (processed !== line) modified = true;
    return processed;
  });

  if (modified) {
    fs.writeFileSync(filePath, newLines.join('\n'), 'utf-8');
    console.log(`[patched] ${filePath}`);
  }
}

// 主入口
const targetDir = process.argv[2] || '.';

if (!fs.existsSync(targetDir)) {
  console.error(`目录不存在: ${targetDir}`);
  process.exit(1);
}

const stat = fs.statSync(targetDir);
if (stat.isFile()) {
  processFile(targetDir);
} else {
  walkDir(targetDir);
}
