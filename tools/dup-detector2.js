// 第二探测器: 不剥公式, 抓"短中文+公式"型重复(如「约束： $...$」重复)
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
    if (inPre) return;
    if (line.startsWith('```') || line.startsWith('|')) return;
    const seen = new Set();
    for (let L = 10; L <= Math.min(80, line.length/2); L++) {
      for (let i = 0; i + L <= line.length; i++) {
        const sub = line.slice(i, i + L);
        if (!hasCJK(sub)) continue;
        if (seen.has(sub)) continue;
        seen.add(sub);
        let cnt = 0, p = 0;
        while ((p = line.indexOf(sub, p)) !== -1) { cnt++; p += L; }
        if (cnt >= 2) {
          console.log(`${f}:${idx+1}: x${cnt} 「${sub.length>50?sub.slice(0,50)+'…':sub}」`);
          total++;
          return;
        }
      }
    }
  });
}
console.log(`\n共 ${total} 行`);
