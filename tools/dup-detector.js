// 检测同行内重复子串(长度>=8 且含中文)的损坏行
const fs = require('fs');
const files = process.argv.slice(2);
const hasCJK = s => /[一-鿿＀-￯　-〿]/.test(s);
let total = 0;
for (const f of files) {
  const lines = fs.readFileSync(f, 'utf8').split('\n');
  let inPre = false;
  lines.forEach((line, idx) => {
    if (line.startsWith('<pre>')) inPre = true;
    if (line.startsWith('</pre>')) { inPre = false; return; }
    if (inPre) return;                       // 跳过 ASCII 图
    if (line.startsWith('```')) return;      // 跳过代码块
    if (line.startsWith('|')) return;         // 跳过表格行
    // 去掉行内 $...$ 公式段后再检测, 避免公式内重复(\text{存活}等)误报
    const stripped = line.replace(/\$[^$]*\$/g, '');
    const seen = new Set();
    for (let L = 8; L <= Math.min(40, stripped.length/2); L++) {
      for (let i = 0; i + L <= stripped.length; i++) {
        const sub = stripped.slice(i, i + L);
        if (!hasCJK(sub)) continue;
        if (seen.has(sub)) continue;
        seen.add(sub);
        let cnt = 0, p = 0;
        while ((p = stripped.indexOf(sub, p)) !== -1) { cnt++; p += L; }
        if (cnt >= 2) {
          console.log(`${f}:${idx+1}: x${cnt} 「${sub}」`);
          total++;
          return;
        }
      }
    }
  });
}
console.log(`\n共 ${total} 行疑似句子重复损坏`);
