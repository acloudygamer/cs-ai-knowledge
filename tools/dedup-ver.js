// 去重首部重复的「> **版本基准**」行: 仅保留第一个, 清理多余空行
const fs = require('fs');
const files = process.argv.slice(2);
let n = 0;
for (const f of files) {
  const lines = fs.readFileSync(f, 'utf8').split('\n');
  let seen = false, changed = false;
  const out = [];
  for (const line of lines) {
    if (line.startsWith('> **版本基准**')) {
      if (seen) { changed = true; continue; }   // 丢弃重复
      seen = true;
    }
    out.push(line);
  }
  // 合并连续 3+ 空行为 2
  let res = out.join('\n').replace(/\n{4,}/g, '\n\n\n');
  if (changed || res !== out.join('\n')) {
    // 仅当确实去重时写回(避免无谓改动)
    if (changed) { fs.writeFileSync(f, res); n++; }
  }
}
console.log(`去重 ${n} 文件`);
