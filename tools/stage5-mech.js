// 阶段5机械变换: 标题改名(定义→本质, 参考存根→代码示例) + 顶部版本基准行
// 用法: node tools/stage5-mech.js <verLine> <file...>
//   verLine 例如 "> **版本基准**：Python 3.12 stable（latest=3.14，新特性章节保留并标注）"
const fs = require('fs');
const verLine = process.argv[2];
const files = process.argv.slice(3);
let touched = 0;
for (const f of files) {
  let s = fs.readFileSync(f, 'utf8');
  const orig = s;
  // 1. 顶部版本行: 在首个 "# 标题" 后插入(若不存在 版本基准)
  s = s.replace(/^(# [^\n]+\n)\n?(?!> \*\*版本基准)/m, (m, p1) => p1 + '\n' + verLine + '\n\n');
  // 2. 标题改名(仅行首精确匹配)
  s = s.replace(/^## 定义$/m, '## 本质');
  s = s.replace(/^## 参考存根$/m, '## 代码示例');
  if (s !== orig) { fs.writeFileSync(f, s); touched++; }
}
console.log(`已处理 ${touched}/${files.length} 文件`);
