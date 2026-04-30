# Flask 基础

## 定义

Flask 是核心极简但扩展生态丰富的 Python WSGI Web 框架，通过松耦合设计让开发者按需选择组件，而非强制捆绑。核心只提供路由、请求/响应对象和上下文本地代理；数据库、会话、认证等功能由扩展按需引入。这与 Django 的"batteries included"哲学形成鲜明对比。

**归约视角**：Flask 的本质是**基于上下文局部变量的请求-响应分派器**——通过 LocalStack 维护请求级上下文，URL 映射表将请求路由到处理函数，处理函数通过上下文代理访问请求数据和会话信息。

## 数学模型

### 请求上下文栈（LocalStack）

Flask 上下文管理基于 `werkzeug.local.LocalStack`，其数学模型是**线程/协程隔离的词法作用域**，可归约为线程局部存储（TLS）的变体。

设 $\text{LS}$ 为 LocalStack，$\text{tid}$ 为当前线程/协程 ID，$\text{stack}[\text{tid}]$ 为该 ID 对应的对象栈：

$$\text{LS.push}(x) \triangleq \text{stack}[\text{tid}].\text{append}(x)$$
$$\text{LS.pop}() \triangleq \text{stack}[\text{tid}].\text{pop}()$$
$$\text{LS.top}() \triangleq \text{stack}[\text{tid}][-1]$$

**隔离性**：若 $\text{tid}_1 \neq \text{tid}_2$，则 $\text{stack}[\text{tid}_1] \cap \text{stack}[\text{tid}_2] = \emptyset$。这保证了不同请求并发执行时，上下文完全隔离。

**归约链**：LocalStack → contextvars（Python 3.7+） → threading.local（Python 2+） → OS-managed TLS 寄存器。Flask 的上下文隔离最终归约到操作系统层面的线程局部存储机制，是这一基础原语在 Web 框架中的具体实现。

### 会话签名（HMAC-SHA256）

Flask session 本质是经密钥签名的 Cookie。设会话数据为 $D$，密钥为 $k$，时间戳为 $t$：

$$\text{session} = \text{base64}(D) \cdot \text{SEP} \cdot \text{base64}(\text{HMAC-SHA256}(k, \text{base64}(D) \cdot t \cdot \text{salt}))$$

服务端验证时，重新计算 HMAC 并与传输值比对：**若不等，则数据被篡改**。

安全性取决于：
- 密钥 $k$ 的熵（应 $\ge 128$ bit 随机数）
- HMAC-SHA256 的抗碰撞性（$2^{256}$ 攻击代价）

**约束**：数据以明文存储在 Cookie 中，仅签名防篡改，不加密保密。因此 session 中只能存用户 ID 等引用符，不得存密码或敏感信息。

### 路由匹配复杂度

Flask 按定义顺序线性扫描路由列表。设路由数为 $R$，最坏情况匹配复杂度：

$$T_{\text{match}} = O(R)$$

Blueprint 注册后，Werkzeug 的 `Map` 维护一个按路径前缀构建的字典跳表（radix trie），典型路径查找均摊 $O(1)$，但 Blueprint 内部仍按注册顺序扫描。

**约束**：当路由数超过 100 时，线性扫描的性能损耗开始显著。此时应使用 Blueprint 并确保高频路由在注册时排在前面。

### 事件驱动的并发模型（归约）

Flask 本身是**同步阻塞 I/O** 模型。单个 worker 在同一时刻只能处理一个请求——其他请求必须排队等待。这意味着：

$$T_{\text{response}} = \sum_{i} T_i^{\text{CPU}} + \sum_{j} T_j^{\text{I/O}}$$

其中 $T^{\text{I/O}}$ 包括数据库查询、外部 API 调用等。**若 $T^{\text{I/O}}$ 占比高（如等待数据库），worker 空闲率就高**。这是 Flask + 同步数据库驱动在高 I/O 场景下性能差的原因。

**归约**：Flask (同步) → Gunicorn (多 worker) → OS 进程调度 → 时间片轮转。真正的并发来自多 worker 进程，而非 Flask 本身。

## 数据流

<pre>
HTTP 请求字节流
    │
    ▼
WSGI Server（Gunicorn / Werkzeug dev server）
    │
    ▼
Flask app.__call__(environ) ──▶ RequestContext 压栈
    │  environ: {REQUEST_METHOD, PATH_INFO, QUERY_STRING, ...}
    │                              │
    │                              ▼
    │                         app.preprocess_request()
    │                         （执行 before_request 钩子）
    │                              │
    ▼                              ▼
URL Resolver（app.url_map）──匹配──▶ 路由处理函数
    │  线性扫描 / Radix Trie 查找
    │                              │
    │                              ▼
    │                         视图函数（业务逻辑）
    │                         通过 request/session/g 访问上下文
    │                              │
    │                              ▼
    │                         蓝图特定 before_request 钩子
    │                              │
    ▼                              ▼
Response 对象 ◀─── app.postprocess_request()
    │  （执行 after_request 钩子）
    ▼
RequestContext 弹栈
    │  触发 teardown_request 钩子
    ▼
WSGI Response（iterable of bytes）
</pre>

**所有权变换**：
- 字节流 → `environ` dict（WSGI 规范）→ `RequestContext`（Flask 封装）
- `g` 对象在请求结束时销毁，不跨请求保留
- `session` 数据经 HMAC 签名后存在客户端 Cookie（服务端无状态）

## 对比参照

| 维度 | Flask | Django | FastAPI |
|------|-------|--------|---------|
| **架构哲学** | 极简核心 + 扩展 | batteries included | 现代类型优先 |
| **上下文模型** | LocalStack（线程/协程隔离） | 请求对象（参数传递） | 依赖注入（显式） |
| **路由定义** | 装饰器（声明式） | URLconf（集中式） | 路径装饰器 + 类型注解 |
| **数据绑定** | 无内置 ORM | ORM 内置 | Pydantic 模型 |
| **异步支持** | 需扩展（Flask 2.3+） | 有限 | 原生 async/await |
| **会话存储** | 签名 Cookie（默认） | 数据库/缓存/Cookie | 无内置 |
| **请求对象** | 全局代理 `request` | 显式参数 `request` | 显式参数 `Request` |

## 机制

### 上下文局部变量的实现原理

`werkzeug.local.LocalStack` 的实现依赖于 Python 的 `contextvars`（Python 3.7+）：

```python
from contextvars import ContextVar
_request_ctx_stack = ContextVar('request_ctx_stack')
```

这意味着：
- 同一进程内，不同请求访问同名变量而互不干扰
- 协程切换时（`asyncio`）上下文自动隔离，无需手动管理
- 上下文栈在请求结束时必须显式 pop，否则 ctx stack 不被 GC（内存泄漏）

**归约视角**：Flask 的 LocalStack 是以下原语链的具体实现：
1. **OS TLS**（`pthread_getspecific`）：操作系统提供的线程局部存储
2. **Python threading.local()**：在 TLS 上封装的 Python 接口
3. **contextvars.ContextVar**：协程安全的上下文隔离（Python 3.7+）
4. **LocalStack**：在 ContextVar 上封装的栈结构

每一层都在前一层的基础上增加了抽象，最终提供了"线程/协程内共享，跨线程/协程隔离"的分层语义。

### 会话签名的安全约束

Flask session 是签名 Cookie——数据以 pickle 序列化后，经 HMAC-SHA256 签名，服务端不存储任何内容。签名验证流程：

```
客户端 Cookie
    │
    ▼  base64 解码 → (data, timestamp, mac_received)
    │
    ▼  重新计算 mac = HMAC-SHA256(secret_key, data + timestamp)
    │
    ▼  恒定时间比对 mac == mac_received ？
    │    是 → session 数据有效
    │    否 → 签名验证失败（数据被篡改）
```

**恒定时间比对**（`hmac.compare_digest`）防止时序攻击：攻击者通过测量响应时间猜测密钥。

**约束**：HMAC 签名只保证完整性（防篡改），不加密内容。Cookie 中的 session 数据是 base64 编码的明文，任何能看到 Cookie 的人都能读取内容。

### Jinja2 模板引擎的核心机制

Jinja2 模板编译为 Python 代码执行。每条模板语句对应一段 Python 代码块：

```jinja2
{% for item in items %}
  <li>{{ item.name }}</li>
{% endfor %}
```

编译后本质上是：
```python
for item in items:
    write('<li>')
    write(str(item.name))
    write('</li>')
```

**编译流程**：模板字符串 → 词法分析（Token） → 语法分析（AST） → Python 源代码 → compile → 代码对象。

**归约视角**：模板引擎本质上是一个**从 DSL（模板语法）到 Python 可执行代码的编译器**。模板中的 `{{ }}` 是插值表达式，`{% %}` 是控制流语句——两者共同构成了一套受限的 Python 子集。这使得模板渲染可以复用 Python 的所有执行优化（字节码缓存、解释器复用）。

**自动转义**：Jinja2 对 HTML 内容默认转义，防止 XSS。转义由 `markupsafe.Markup` 实现——字符串被标记为"安全"后，跳过转义步骤。

### 蓝图（Blueprint）的命名空间隔离

Blueprint 在 Flask 中创建独立的 URL 命名空间和视图集合：

- `url_prefix` 为 Blueprint 下所有路由批量添加路径前缀
- `endpoint` 默认以蓝图名为前缀（如 `api.health`），避免不同蓝图之间的端点冲突
- Blueprint 可以有自己的 `before_request`/`after_request` 钩子，作用于该蓝图下所有路由

**设计动机**：Flask 的极简核心不提供模块化机制，Blueprint 是补充方案。将大型应用拆为多个 Blueprint，等价于将单体应用分解为多个松耦合的子应用——各 Blueprint 独立开发测试，最后注册到主应用。

### 错误处理的解耦设计

Flask 的 `@app.errorhandler` 捕获 Werkzeug 的 HTTPException 或任意 Python 异常：

- `abort(404)` 抛出 `NotFound` 异常，由 `errorhandler(404)` 处理
- 业务逻辑错误（数据验证失败、权限不足）应返回 `jsonify({"error": "..."}, 400)`，而非 `abort`——因为 `abort` 会跳过视图函数的后续代码
- 未被捕获的异常最终由 `app.handle_exception()` 和 `app.handle_user_exception()` 处理

**约束**：错误处理器中无法访问原始请求上下文（如 `request` 代理），因为错误可能在请求上下文弹出之后触发。若需要请求数据，必须在视图函数中保存到 `g` 对象。

## 参考存根

```python
from flask import Flask, g, session, request, jsonify, abort
import hmac, hashlib

app = Flask(__name__)

@app.before_request
def before():
    g.db_conn = get_db_connection()

@app.teardown_request
def teardown(exc):
    if hasattr(g, 'db_conn'):
        g.db_conn.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    session["user_id"] = data["username"]  # 签名 Cookie
    return jsonify({"status": "ok"})

@app.route("/protected")
def protected():
    if "user_id" not in session:
        abort(401)
    return jsonify({"user": session["user_id"]})

# 验证签名 cookie（在请求外测试）
with app.test_request_context("/"):
    print(session)

# HMAC 签名验证（防篡改）
def verify_mac(secret_key, data, mac):
    expected = hmac.new(secret_key, data, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, mac)  # 恒定时间比对，防时序攻击
```
