# this 与调用约定

> 前置：[02-闭包与作用域链](./02-闭包与作用域链.md) · 后续：[04-属性描述符与元编程](./04-属性描述符与元编程.md)

> **版本基准**：Node 24 stable / Node 26 latest。本篇示例实测环境：Node v24.13.1（V8 13.6），Windows x64。

## 本质

`this` 是**函数被调用时**由调用方决定的一个隐式绑定。它与名字查找规则相反：一个函数能看见哪些**变量**由它写在哪儿决定（词法作用域，见 [02-闭包与作用域链](./02-闭包与作用域链.md)），但它的 `this` 指向谁由**怎么调用它**决定。

这是 JavaScript 里唯一的一处动态作用域。它之所以存在，是为了满足一个宿主需求：**调用方需要在调用时把上下文传给回调**。事件处理器要知道"哪个元素被点了"，`Array.prototype.map` 的回调要能拿到额外的 `thisArg`——如果 `this` 由定义处决定，这些信息就只能靠额外参数传递。

理解 `this` 只需要记住一句话：**看调用点，不看定义点**。

## 机制

### 四条绑定规则

按优先级从高到低：

| 优先级 | 规则 | 形态 | `this` 指向 |
|---|---|---|---|
| 1 | `new` 绑定 | `new F()` | 新建的那个对象 |
| 2 | 显式绑定 | `f.call(x)` / `f.apply(x)` / `f.bind(x)` | 传入的 `x` |
| 3 | 隐式绑定 | `obj.f()` | `obj`（点号左边那个） |
| 4 | 默认绑定 | `f()` | 严格模式 `undefined`；宽松模式全局对象 |

```console
$ node -e 'function who(){ return this===undefined?"undefined":(this===globalThis?"globalThis":this.tag) } console.log(who(), "|", {tag:"obj",m:who}.m())'
globalThis | obj
```

同一次运行里，同一个 `who` 因为调用形式不同，`this` 一次是全局对象、一次是 `obj`——**函数本身没有变**。

### 隐式绑定最脆弱的环节：提取

`this` 由**调用点的语法形态**决定，所以把方法取出来单独调用，`obj.` 这个前缀就没了：

```console
$ node -e 'const obj={tag:"obj", m:function(){return this.tag}}; const ext=obj.m; console.log(ext())'
undefined
```

`ext()` 是默认绑定，`this` 成了全局对象（宽松模式），`this.tag` 自然是 `undefined`。这就是 `setTimeout(obj.method, 0)`、`arr.forEach(obj.method)`、把方法作为回调传递时丢失 `this` 的机制——**方法在传出去的那一刻就不再是"方法"了**。

### 显式绑定与 `new` 的优先级

```console
$ node -e 'function who(){ return this.tag } const b = who.bind({tag:"bound"}); console.log(b(), b.call({tag:"other"}))'
bound bound
```

`bind` 返回一个**永久绑定**的新函数——此后无论怎么调用（包括 `.call`）都改不掉。但 `new` 比它更高：

```console
$ node -e 'function C(){ this.tag="new" } const BC = C.bind({tag:"bound"}); console.log(new BC().tag)'
new
```

`new` 忽略 `bind` 指定的 `this`，因为它必须自己创建对象。这条优先级在写类工厂时偶尔会咬人。

`call` 与 `apply` 的区别只在传参形式（`call(thisArg, a, b)` 对 `apply(thisArg, [a, b])`）；`bind` 返回新函数，前两者立即调用。

### 严格模式改变默认绑定

```console
$ node --input-type=module -e 'function who(){ return this===undefined?"undefined":"globalThis" } console.log(who())'
undefined
```

宽松模式把裸调用的 `this` 补成全局对象（历史行为：让页面里的函数能直接访问 `window`）；严格模式保持 `undefined`，让"忘了绑定"立刻暴露。**ESM 与类体恒为严格模式**（见 [01-语言核心/02-绑定与类型](../01-语言核心/02-绑定与类型.md)），所以模块里的裸调用拿到的就是 `undefined`。

### 箭头函数：退出这套规则

箭头函数**没有自己的 `this`**，它沿作用域链取定义处外层的 `this`：

```console
$ node -e 'const h={tag:"holder", arrow:()=>this===undefined?"undefined":this.tag, normal(){return this.tag}}; console.log(h.arrow(), h.normal())'
undefined holder
```

`h.normal()` 走隐式绑定得到 `h`；`h.arrow()` 忽略调用点，取的是模块顶层那个 `this`（`undefined`）。这也解释了 [01-语言核心/04-函数](../01-语言核心/04-函数.md) 里那三条——没有 `this`、没有 `arguments`、不能 `new`——的同一个来源：箭头函数不建立自己的调用上下文。

## 连接：四种绑定对照

| 调用形式 | 规则 | 典型场景 | 常见事故 |
|---|---|---|---|
| `f()` | 默认 | 普通函数调用 | 严格模式 `this` 为 `undefined` 而报错 |
| `o.f()` | 隐式 | 方法调用 | 方法被提取后丢失 |
| `f.call/apply/bind(x)` | 显式 | 借用方法、固定上下文 | 过度使用 `bind` 造成难追踪的绑定 |
| `new f()` | `new` | 构造对象 | 构造器 `return` 对象会覆盖 `this` |
| `() => this` | 词法 | 回调中保留外层 `this` | 需要动态 `this` 时误用箭头函数 |

**现代写法**：类方法用普通函数定义（`this` 由调用点决定是想要的），回调用箭头函数（继承外层 `this` 是想要的）。这个分工覆盖了绝大多数场景，`bind` 主要留给"把方法作为回调传出去"的边界。

## 边界

- **`this` 与"对象"无关**：`obj.f()` 的 `this` 是 `obj` 不是 `f`，`f` 可以从任何对象上借用（`Array.prototype.slice.call(arguments)` 就是这种借用）。
- **`this` 不是作用域链的一部分**：它不参与名字查找。`this.x` 是属性查找（走原型链），`x` 是名字查找（走作用域链），两者无关。
- **不要在箭头函数里期待动态 `this`**：事件处理器、`Vue`/`React` 的旧式生命周期钩子等依赖动态 `this` 的位置必须用普通函数。
- **`this` 在模块顶层是 `undefined`**（ESM）或 `module.exports`（CommonJS）——这不是笔误，是两种模块系统的既定差异。

---

> 前置：[02-闭包与作用域链](./02-闭包与作用域链.md) · 后续：[04-属性描述符与元编程](./04-属性描述符与元编程.md)——属性除了"值"，还有"行为"
