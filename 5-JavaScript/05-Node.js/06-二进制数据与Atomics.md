# 二进制数据与 Atomics

## ArrayBuffer

ArrayBuffer 表示固定长度的二进制数据缓冲区。

### 基本用法

```javascript
// 创建缓冲区
const buffer = new ArrayBuffer(16);
console.log(buffer.byteLength);  // 16

// 切片
const slice = buffer.slice(0, 8);
console.log(slice.byteLength);   // 8
```

### 类型化数组

```javascript
const buffer = new ArrayBuffer(8);

// 不同类型视图
const int8 = new Int8Array(buffer);
const uint8 = new Uint8Array(buffer);
const int16 = new Int16Array(buffer);
const uint16 = new Uint16Array(buffer);
const int32 = new Int32Array(buffer);
const uint32 = new Uint32Array(buffer);
const float32 = new Float32Array(buffer);
const float64 = new Float64Array(buffer);

int8[0] = 127;
int8[1] = -128;
console.log(int8.length);  // 8（8 字节 / 1）
console.log(int32.length); // 2（8 字节 / 4）
```

### 字节序

```javascript
const buffer = new ArrayBuffer(4);
const view = new Uint16Array(buffer);

// 小端序（默认）
view[0] = 0x1234;
console.log(view[0].toString(16));  // 1234

// 检测字节序
const isLittleEndian = new Uint8Array(new Uint16Array([1]).buffer)[0] === 1;
console.log('Little Endian:', isLittleEndian);

// 大端序写入
const bigEndian = new DataView(buffer);
bigEndian.setUint16(0, 0x1234, false);  // false = 大端序
```

---

## DataView

DataView 提供更灵活的读写控制。

### 基本用法

```javascript
const buffer = new ArrayBuffer(12);
const view = new DataView(buffer);

// 写入不同类型
view.setInt8(0, 127);
view.setUint8(1, 255);
view.setInt16(2, 1000, true);   // true = 小端序
view.setFloat32(4, 3.14, true);
view.setFloat64(6, 2.718281828, true);

// 读取
console.log(view.getInt8(0));        // 127
console.log(view.getUint8(1));       // 255
console.log(view.getInt16(2, true)); // 1000
console.log(view.getFloat32(4, true));  // 3.14
console.log(view.getFloat64(6, true));  // 2.718281828
```

---

## TypedArray 常用操作

### 数组操作

```javascript
const arr = new Uint8Array([1, 2, 3, 4, 5]);

// 迭代
for (const value of arr) { console.log(value); }
arr.forEach(v => console.log(v));

// 子数组
const sub = arr.subarray(1, 3);  // 类似 slice，但不复制
console.log([...sub]);  // [2, 3]

// 复制
const copy = new Uint8Array(arr);
console.log([...copy]);  // [1, 2, 3, 4, 5]
```

### 搜索和排序

```javascript
const arr = new Uint16Array([3, 1, 2, 1, 5]);

// 查找
console.log(arr.indexOf(2));     // 2
console.log(arr.includes(3));     // true
console.log(arr.find(v => v > 2));  // 3

// 排序
arr.sort((a, b) => a - b);
console.log([...arr]);  // [1, 1, 2, 3, 5]
```

### 转换

```javascript
const arr = new Uint8Array([72, 101, 108, 108, 111]);

// 转字符串
const str = String.fromCharCode(...arr);
console.log(str);  // 'Hello'

// 从字符串创建
const fromStr = new Uint8Array('Hello'.split('').map(c => c.charCodeAt(0)));
console.log([...fromStr]);  // [72, 101, 108, 108, 111]

// 转普通数组
const normalArr = Array.from(arr);
const normalArr2 = [...arr];
```

---

## Blob

Blob 表示不可变的原始二进制数据。

### 基本用法

```javascript
// 创建 Blob
const blob = new Blob(['Hello, World!'], { type: 'text/plain' });
console.log(blob.size);  // 13
console.log(blob.type);  // 'text/plain'

// 从 TypedArray 创建
const arr = new Uint8Array([1, 2, 3]);
const blobFromArray = new Blob([arr], { type: 'application/octet-stream' });

// 切片
const slice = blob.slice(0, 5, { type: 'text/plain' });
```

### Blob 与其他格式转换

```javascript
// Blob -> ArrayBuffer
const arrayBuffer = await blob.arrayBuffer();
const uint8 = new Uint8Array(arrayBuffer);

// Blob -> Text
const text = await blob.text();

// Blob -> Data URL
const reader = new FileReader();
reader.onload = () => console.log(reader.result);
reader.readAsDataURL(blob);

// Blob -> ReadableStream (Node.js)
const { Readable } = require('stream');
const readable = Readable.from(blob.stream());
```

### 文件下载

```javascript
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// 使用
const blob = new Blob(['Download content'], { type: 'text/plain' });
downloadBlob(blob, 'test.txt');
```

---

## File / FileReader

### File

```javascript
// 从 input 读取
const file = fileInput.files[0];
console.log(file.name);      // 'example.txt'
console.log(file.size);      // 1024
console.log(file.type);      // 'text/plain'
console.log(file.lastModified);  // 1699999999999

// 创建 File
const file = new File(['content'], 'example.txt', { type: 'text/plain' });
```

### FileReader

```javascript
const reader = new FileReader();

// 读取为文本
reader.readAsText(file);
reader.onload = () => console.log(reader.result);

// 读取为 ArrayBuffer
reader.readAsArrayBuffer(file);
reader.onload = () => console.log(new Uint8Array(reader.result));

// 读取为 Data URL
reader.readAsDataURL(file);
reader.onload = () => console.log(reader.result);

// 读取为 Binary String（已废弃）
reader.readAsBinaryString(file);
```

---

## Atomics

Atomics 提供原子操作，用于在 SharedArrayBuffer 中进行线程安全的操作。

### SharedArrayBuffer

```javascript
// 创建共享缓冲区
const sharedBuffer = new SharedArrayBuffer(4);
const int32 = new Int32Array(sharedBuffer);

int32[0] = 0;
console.log(int32[0]);  // 0
```

### 原子操作

```javascript
const shared = new SharedArrayBuffer(4);
const arr = new Int32Array(shared);
arr[0] = 0;

// 原子加法
Atomics.add(arr, 0, 10);    // 返回旧值 0，arr[0] 变为 10
console.log(arr[0]);       // 10

// 原子减法
Atomics.sub(arr, 0, 3);    // 返回旧值 10，arr[0] 变为 7
console.log(arr[0]);       // 7

// 原子交换
Atomics.exchange(arr, 0, 100);  // 返回 7，arr[0] 变为 100
console.log(arr[0]);           // 100

// 原子比较交换（CAS）
Atomics.compareExchange(arr, 0, 100, 200);  // 如果 arr[0] === 100，设为 200
console.log(arr[0]);                      // 200

Atomics.compareExchange(arr, 0, 100, 300);  // 如果 arr[0] !== 100，不变
console.log(arr[0]);                      // 200
```

### 原子加载和存储

```javascript
const shared = new SharedArrayBuffer(4);
const arr = new Int32Array(shared);
arr[0] = 42;

// 原子加载
console.log(Atomics.load(arr, 0));  // 42

// 原子存储
Atomics.store(arr, 0, 100);  // 返回 100
console.log(arr[0]);         // 100
```

### 原子逻辑操作

```javascript
const shared = new SharedArrayBuffer(4);
const arr = new Int32Array(shared);
arr[0] = 0b1010;  // 二进制 1010

// AND
Atomics.and(arr, 0, 0b1100);  // arr[0] = 0b1000
console.log(arr[0]);          // 8

// OR
Atomics.or(arr, 0, 0b0011);   // arr[0] = 0b1011
console.log(arr[0]);          // 11

// XOR
Atomics.xor(arr, 0, 0b0101);  // arr[0] = 0b1110
console.log(arr[0]);          // 14
```

### 等待和通知

```javascript
const shared = new SharedArrayBuffer(4);
const arr = new Int32Array(shared);

// 工作线程
function worker() {
  // 等待 arr[0] 变为非零值
  Atomics.wait(arr, 0, 0);  // 阻塞，直到条件满足
  console.log('Wake up!');
}

// 主线程
arr[0] = 1;
Atomics.notify(arr, 0, 1);  // 唤醒 1 个等待的线程

// 带超时的等待
Atomics.wait(arr, 0, 0, 1000);  // 最多等待 1000ms
```

### isLockFree

```javascript
// 检查是否使用锁自由算法
console.log(Atomics.isLockFree(1));  // true（大多数平台）
console.log(Atomics.isLockFree(2));  // true
console.log(Atomics.isLockFree(3)); // false（通常）
console.log(Atomics.isLockFree(4)); // true
console.log(Atomics.isLockFree(8)); // true
```

---

## 实际应用场景

### 1. WebGL 纹理数据

```javascript
function createTexture(width, height) {
  const data = new Uint8Array(width * height * 4);

  for (let i = 0; i < width * height; i++) {
    data[i * 4] = 255;     // R
    data[i * 4 + 1] = 0;   // G
    data[i * 4 + 2] = 0;   // B
    data[i * 4 + 3] = 255; // A
  }

  return data;
}

const textureData = createTexture(256, 256);
const texture = gl.createTexture();
gl.bindTexture(gl.TEXTURE_2D, texture);
gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 256, 256, 0, gl.RGBA, gl.UNSIGNED_BYTE, textureData);
```

### 2. 网络协议解析

```javascript
class PacketParser {
  constructor(buffer) {
    this.view = new DataView(buffer);
    this.offset = 0;
  }

  readUint8() {
    return this.view.getUint8(this.offset++);
  }

  readUint16() {
    const val = this.view.getUint16(this.offset, true);
    this.offset += 2;
    return val;
  }

  readString(length) {
    const bytes = new Uint8Array(this.buffer, this.offset, length);
    this.offset += length;
    return new TextDecoder().decode(bytes);
  }

  readPacket() {
    const type = this.readUint8();
    const length = this.readUint16();
    const data = this.readString(length);
    return { type, length, data };
  }
}
```

### 3. 进程间通信（Worker）

```javascript
// 主线程
const shared = new SharedArrayBuffer(4);
const arr = new Int32Array(shared);

const worker = new Worker('worker.js');
worker.postMessage({ shared });

// 监听结果
worker.onmessage = (e) => {
  console.log('Result:', e.data);
};

// 通知 worker 可以开始
Atomics.store(arr, 0, 1);
Atomics.notify(arr, 0, 1);

// worker.js
self.onmessage = (e) => {
  const { shared } = e.data;
  const arr = new Int32Array(shared);

  // 等待主线程准备好
  Atomics.wait(arr, 0, 0);

  // 处理数据
  const result = compute();
  self.postMessage(result);

  // 通知完成
  Atomics.store(arr, 0, 0);
  Atomics.notify(arr, 0, 1);
};
```

### 4. 高性能计数器

```javascript
class AtomicCounter {
  constructor() {
    this.buffer = new SharedArrayBuffer(4);
    this.arr = new Int32Array(this.buffer);
    Atomics.store(this.arr, 0, 0);
  }

  increment() {
    return Atomics.add(this.arr, 0, 1);
  }

  decrement() {
    return Atomics.sub(this.arr, 0, 1);
  }

  get value() {
    return Atomics.load(this.arr, 0);
  }

  reset() {
    Atomics.store(this.arr, 0, 0);
  }
}
```

---

## Node.js 中的二进制

### Buffer

```javascript
// 创建 Buffer
const buf = Buffer.alloc(16);
const bufFromString = Buffer.from('Hello');
const bufFromArray = Buffer.from([72, 101, 108, 108, 111]);

// 字符串编解码
const encoded = Buffer.from('你好', 'utf-8');
console.log(encoded.length);  // 6
console.log(encoded.toString('utf-8'));  // '你好'

// 读写
buf.writeUInt8(0x41, 0);  // 写入字节
console.log(buf.readUInt8(0));  // 65 ('A')

// 拼接
const buf1 = Buffer.from('Hello');
const buf2 = Buffer.from(' World');
const combined = Buffer.concat([buf1, buf2]);
console.log(combined.toString());  // 'Hello World'
```

### 处理二进制协议

```javascript
const buf = Buffer.alloc(12);

// 写入协议头
buf.writeUInt32BE(0x12345678, 0);  // 大端序
buf.writeUInt32BE(Date.now(), 4);  // 时间戳
buf.writeUInt16BE(100, 8);          // 长度
buf.writeUInt16BE(0, 10);           // 校验和（待计算）

// 计算校验和
let checksum = 0;
for (let i = 0; i < 10; i++) {
  checksum += buf[i];
}
buf.writeUInt16BE(checksum & 0xFFFF, 10);
```

---

## 总结

| 类型 | 用途 | 大小 |
|------|------|------|
| Int8Array | 有符号字节 | 1 字节 |
| Uint8Array | 无符号字节 | 1 字节 |
| Int16Array | 有符号短整型 | 2 字节 |
| Uint16Array | 无符号短整型 | 2 字节 |
| Int32Array | 有符号整型 | 4 字节 |
| Uint32Array | 无符号整型 | 4 字节 |
| Float32Array | 单精度浮点 | 4 字节 |
| Float64Array | 双精度浮点 | 8 字节 |

| Atomics 方法 | 描述 |
|-------------|------|
| load/Store | 原子加载和存储 |
| add/sub | 原子加减 |
| and/or/xor | 原子位运算 |
| exchange | 原子交换 |
| compareExchange | CAS 操作 |
| wait/notiry | 线程同步 |
