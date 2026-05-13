#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

function formatText(text) {
  // 使用 Unicode 私有字符作为占位符，绝对不会和文件内容冲突
  const BGN = '\uE000';
  const END = '\uE001';

  // 1. 保护代码块：屏蔽 ```多行

  const codes = [];
  text = text.replace(/(`{1,3})[\s\S]*?\1/g, match => {
    codes.push(match);
    return `${BGN}C${codes.length - 1}${END}`;
  });

  // 2. 保护并提取公式：严格提取 $...$（避开转义的 \$ 和块公式 $$）
  const formulas = [];
  text = text.replace(/(?<!\\|\$)(\$[^$\n]+?\$)(?!\$)/g, match => {
    formulas.push(match);
    return `${BGN}F${formulas.length - 1}${END}`;
  });

  const formulaRegexStr = `${BGN}F\\d+${END}`;

  // 3. 收紧现有空格：如果公式两端原本就有 2 个以上的空格，强制压缩为 1 个
  text = text.replace(new RegExp(` {2,}(${formulaRegexStr})`, 'g'), ' $1');
  text = text.replace(new RegExp(`(${formulaRegexStr}) {2,}`, 'g'), '$1 ');

  // 4. 处理【前边界】：如果前面【不是】空白、左括号、引号或 Markdown 特殊符号，则加空格
  const excludeBefore = `[^\\s\\(\\[\\{<"'“‘（【《*_\\-~]`;
  text = text.replace(new RegExp(`(${excludeBefore})(${formulaRegexStr})`, 'g'), '$1 $2');

  // 5. 处理【后边界】：如果后面【不是】空白、右括号、标点符号、引号或 Markdown 特殊符号，则加空格
  const excludeAfter = `[^\\s\\.,;:!\\?\\)\\]\\}>"'”’，。！？；：、）】》*_\\-~]`;
  text = text.replace(new RegExp(`(${formulaRegexStr})(${excludeAfter})`, 'g'), '$1 $2');

  // 6. 还原公式
  text = text.replace(/\uE000F(\d+)\uE001/g, (_, i) => formulas[i]);

  // 7. 还原代码块
  text = text.replace(/\uE000C(\d+)\uE001/g, (_, i) => codes[i]);

  return text;
}

// 遍历目录或文件
function processTarget(targetPath) {
  const stat = fs.statSync(targetPath);
  
  if (stat.isDirectory()) {
    const entries = fs.readdirSync(targetPath, { withFileTypes: true });
    for (const entry of entries) {
      processTarget(path.join(targetPath, entry.name));
    }
  } else if (stat.isFile() && targetPath.endsWith('.md')) {
    const oldText = fs.readFileSync(targetPath, 'utf-8');
    const newText = formatText(oldText);
    
    if (oldText !== newText) {
      fs.writeFileSync(targetPath, newText, 'utf-8');
      console.log(`[已排版] ${targetPath}`);
    }
  }
}

// 运行脚本
const target = process.argv[2] || '.';
if (!fs.existsSync(target)) {
  console.error('路径不存在！');
  process.exit(1);
}

processTarget(target);