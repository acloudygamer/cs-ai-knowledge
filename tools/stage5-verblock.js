// 删除尾部冗余版本标注块: 「\n---\n\n**版本标注**：本文内容为...无版本特定差异。」
const fs = require('fs');
const { execSync } = require('child_process');
const files = execSync('find 2-Python 3-C++ -name "*.md" ! -name "README.md"', { encoding: 'utf8' }).trim().split('\n');
let n = 0;
for (const f of files) {
  let s = fs.readFileSync(f, 'utf8');
  const o = s;
  s = s.replace(/\n+---\n\n\*\*版本标注\*\*：本文内容为[^]*?无版本特定差异。\n?$/, '\n');
  if (s !== o) { fs.writeFileSync(f, s); n++; }
}
console.log(`删尾部版本标注块: ${n} 文件`);
