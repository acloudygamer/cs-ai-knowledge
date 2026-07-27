// 批量: **归约终点**： → > **洞察**：
const fs = require('fs');
const { execSync } = require('child_process');
const files = execSync('find 2-Python 3-C++ -name "*.md" ! -name "README.md"', { encoding: 'utf8' }).trim().split('\n');
let n = 0, tot = 0;
for (const f of files) {
  const s = fs.readFileSync(f, 'utf8');
  let c = 0;
  const out = s.replace(/^\*\*归约终点\*\*：/gm, () => { c++; return '> **洞察**：'; });
  if (c) { fs.writeFileSync(f, out); n++; tot += c; }
}
console.log(`归约终点→洞察: ${n} 文件, ${tot} 处`);
