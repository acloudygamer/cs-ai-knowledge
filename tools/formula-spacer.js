#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

function formatText(text) {
  const BGN = '\uE000';
  const END = '\uE001';

  // 1. 保护代码块
  const codes = [];
  text = text.replace(/(`{1,3})[\s\S]*?\1/g, match => {
    codes.push(match);
    return `${BGN}C${codes.length - 1}${END}`;
  });

  // 2. 保护并提取公式
  const formulas = [];
  text = text.replace(/(?<!\\|\$)(\$[^$\n]+?\$)(?!\$)/g, match => {
    formulas.push(match);
    return `${BGN}F${formulas.length - 1}${END}`;
  });

  const formulaRegexStr = `${BGN}F\\d+${END}`;

  // 3. 收紧多余空格
  text = text.replace(new RegExp(` {2,}(${formulaRegexStr})`, 'g'), ' $1');
  text = text.replace(new RegExp(`(${formulaRegexStr}) {2,}`, 'g'), '$1 ');

  // 4. 处理【前边界】（核心修正！）
  // 移除了全角标点！现在遇到“检验：$x$”，会被强制修正为“检验： $x$”以保证渲染。
  // 只有遇到真正在视觉上包裹公式的左括号、左引号等，才会允许紧贴。
  const excludeBefore = `[^\\s\\(\\[\\{<"'“‘（【《*_\\-~]`;
  text = text.replace(new RegExp(`(${excludeBefore})(${formulaRegexStr})`, 'g'), '$1 $2');

  // 5. 处理【后边界】
  // 后边界保持不变：公式后面紧跟句号、逗号等标点是合法的，不会破坏渲染，不加空格。
  const excludeAfter = `[^\\s\\.,;:!\\?\\)\\]\\}>"'”’，。！？；：、）】》*_\\-~]`;
  text = text.replace(new RegExp(`(${formulaRegexStr})(${excludeAfter})`, 'g'), '$1 $2');

  // 【新增的一步：强制紧贴后置标点！】
  // 如果公式和标点符号之间有任何空格，无情地删掉它们，实现绝对紧贴。
  const tightAfterPunctuation = `([\\.,;:!\\?\\)\\]\\}>"'”’，。！？；：、）】》])`;
  text = text.replace(new RegExp(`(${formulaRegexStr})\\s+${tightAfterPunctuation}`, 'g'), '$1$2');
  // 6. 还原公式
  text = text.replace(/\uE000F(\d+)\uE001/g, (_, i) => formulas[i]);

  // 7. 还原代码块
  text = text.replace(/\uE000C(\d+)\uE001/g, (_, i) => codes[i]);

  return text;
}

// 遍历及文件处理逻辑
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
      console.log(`[已排版 - 渲染安全] ${targetPath}`);
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