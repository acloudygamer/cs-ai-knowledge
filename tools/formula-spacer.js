#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

function formatText(text) {
  const BGN = '\uE000';
  const END = '\uE001';

  // ==========================================
  // 阶段 1：保护与提取（代码块与块级公式）
  // ==========================================
  
  // 1. 保护代码块（避免里面的 $ 符号被误改）
  const codes = [];
  text = text.replace(/(`{1,3})[\s\S]*?\1/g, match => {
    codes.push(match);
    return `${BGN}C${codes.length - 1}${END}`;
  });

  // 2. 保护块级公式（$$...$$）并【强制前后空行】
  const blockFormulas = [];
  text = text.replace(/(\$\$[\s\S]+?\$\$)/g, match => {
    blockFormulas.push(match);
    return `${BGN}B${blockFormulas.length - 1}${END}`;
  });

  const blockRegexStr = `${BGN}B\\d+${END}`;
  // 核心逻辑：无论原本挤在一起还是空了太多行，强制收敛为有且仅有一个空行 (\n\n)
  text = text.replace(new RegExp(`([^\\n])\\s*(${blockRegexStr})`, 'g'), '$1\n\n$2');
  text = text.replace(new RegExp(`(${blockRegexStr})\\s*([^\\n])`, 'g'), '$1\n\n$2');

  // ==========================================
  // 阶段 2：保护与排版（行内公式）
  // ==========================================

  // 3. 保护并提取行内公式（$...$）
  const formulas = [];
  text = text.replace(/(?<!\\|\$)(\$[^$\n]+?\$)(?!\$)/g, match => {
    formulas.push(match);
    return `${BGN}F${formulas.length - 1}${END}`;
  });

  const formulaRegexStr = `${BGN}F\\d+${END}`;

  // 4. 强制收紧多余的空格（原稿里的连续空格被压缩为 1 个）
  text = text.replace(new RegExp(` {2,}(${formulaRegexStr})`, 'g'), ' $1');
  text = text.replace(new RegExp(`(${formulaRegexStr}) {2,}`, 'g'), '$1 ');

  // 5. 处理【前边界】：遇到文字和冒号等强行加空格，确保渲染引擎识别
  const excludeBefore = `[^\\s\\(\\[\\{<"'“‘（【《*_\\-~]`;
  text = text.replace(new RegExp(`(${excludeBefore})(${formulaRegexStr})`, 'g'), '$1 $2');

  // 6. 处理【后边界】：除了标点符号和括号，其余强行加空格
  const excludeAfter = `[^\\s\\.,;:!\\?\\)\\]\\}>"'”’，。！？；：、）】》*_\\-~]`;
  text = text.replace(new RegExp(`(${formulaRegexStr})(${excludeAfter})`, 'g'), '$1 $2');

  // 7. 终极补丁【强制紧贴后置标点】：清除原稿中标点前面的多余空格！
  const tightAfterPunctuation = `([\\.,;:!\\?\\)\\]\\}>"'”’，。！？；：、）】》])`;
  text = text.replace(new RegExp(`(${formulaRegexStr})\\s+${tightAfterPunctuation}`, 'g'), '$1$2');

  // ==========================================
  // 阶段 3：全量还原
  // ==========================================

  text = text.replace(/\uE000F(\d+)\uE001/g, (_, i) => formulas[i]);
  text = text.replace(/\uE000B(\d+)\uE001/g, (_, i) => blockFormulas[i]);
  text = text.replace(/\uE000C(\d+)\uE001/g, (_, i) => codes[i]);

  return text;
}

// 遍历及文件读写逻辑
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
      console.log(`[已完美排版] ${targetPath}`);
    }
  }
}

// 运行入口
const target = process.argv[2] || '.';
if (!fs.existsSync(target)) {
  console.error('路径不存在！');
  process.exit(1);
}

processTarget(target);