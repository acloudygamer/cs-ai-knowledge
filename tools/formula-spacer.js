#!/usr/bin/env node
/**
 * 公式两端空格填充脚本
 *
 * 遍历所有 .md 文件，确保 $...$ 和 $$...$$ 公式在邻近中文字符时两端有空格。
 * 规则：
 *   - 公式前若紧邻中文字符，补一个空格
 *   - 公式后若紧邻中文字符，补一个空格
 *
 * 用法：node formula-spacer.js [目录]
 */

const fs = require('fs');
const path = require('path');

// 中文字符 Unicode 范围
const CHINESE_REGEX = /[一-鿿　-〿！-￯]/;

// 检查一个字符是否为中文（包括中日韩统一表意文字、全角标点）
function isChinese(char) {
  return CHINESE_REGEX.test(char);
}

// 在 str 的 pos 位置前插入空格（仅当前一个字符非空白时）
function padLeft(str, pos) {
  if (pos === 0) return str;
  const prev = str[pos - 1];
  if (/\s/.test(prev)) return str; // 已有空格/换行
  if (isChinese(prev)) return ' ' + str; // 左边是中文，补空格
  return str;
}

// 在 str 的 pos 位置后（即 pos 为公式结束索引）插入空格（仅当后一个字符非空白时）
function padRight(str, pos) {
  if (pos >= str.length - 1) return str;
  const next = str[pos + 1];
  if (/\s/.test(next)) return str; // 已有空格/换行
  if (isChinese(next)) return str + ' '; // 右边是中文，补空格
  return str;
}

// 处理行内公式 $...$
function processInlineFormula(line) {
  let result = line;
  // 匹配 $...$，支持转义 \$
  const regex = /(?<!\\)\$(?!\$)((?:[^$\\]|\\.)+?)(?<!\\)\$/g;
  let match;
  let offset = 0;

  while ((match = regex.exec(line)) !== null) {
    const fullMatch = match[0];
    const start = match.index;
    const end = start + fullMatch.length - 1;

    const before = line.substring(0, start);
    const after = line.substring(end + 1);

    let newBefore = before;
    let newAfter = after;

    // 检查左边
    if (before.length > 0) {
      const lastChar = before[before.length - 1];
      if (isChinese(lastChar)) {
        newBefore = before + ' ';
      }
    }

    // 检查右边
    if (after.length > 0) {
      const firstChar = after[0];
      if (isChinese(firstChar)) {
        newAfter = ' ' + after;
      }
    }

    const newLine = newBefore + fullMatch + newAfter;
    result = result.replace(line, newLine);
    line = newLine;
  }
  return result;
}

// 处理整行（$$...$$ 块公式）
function processBlockFormula(line) {
  let result = line;
  // 匹配 $$...$$
  const regex = /\$\$((?:[^$\\]|\\.)+?)\$\$/g;
  let match;

  while ((match = regex.exec(line)) !== null) {
    const fullMatch = match[0];
    const start = match.index;
    const end = start + fullMatch.length - 1;

    const before = line.substring(0, start);
    const after = line.substring(end + 1);

    let newBefore = before;
    let newAfter = after;
    let changed = false;

    // 检查左边
    if (before.length > 0) {
      const lastChar = before[before.length - 1];
      if (isChinese(lastChar)) {
        newBefore = before + ' ';
        changed = true;
      }
    }

    // 检查右边
    if (after.length > 0) {
      const firstChar = after[0];
      if (isChinese(firstChar)) {
        newAfter = ' ' + after;
        changed = true;
      }
    }

    if (changed) {
      const newLine = newBefore + fullMatch + newAfter;
      result = result.replace(line, newLine);
      line = newLine;
    }
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
