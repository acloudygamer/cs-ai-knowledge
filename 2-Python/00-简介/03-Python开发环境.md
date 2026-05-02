# 开发环境

## 定义

Python 开发环境是**字节码执行 + 包解析 + 符号表管理**的运行时基础。安装 Python 本质是将 CPython 解释器（`python.exe`）及其标准库部署到本地文件系统，并通过 `PATH` 环境变量使解释器可被发现。虚拟环境通过目录隔离 + `sys.path` 调整实现依赖隔离。

## 数学模型

### 解释器路径解析

执行 `python script.py` 时，shell 查找 `python` 可执行文件的过程是**首个匹配原则**：

$$\text{python\_path}(python) = \min \{ p_i \in PATH \mid \exists python.exe \in p_i \}$$

其中 $\min$ 按 $PATH$ 中的顺序定义（从左到右扫描，返回第一个匹配）。

**约束**：若存在多个 Python 安装，后加入 `PATH` 的目录优先级更高。这导致：
- 后安装的 Python 会"遮蔽"先安装的版本
- `python --version` 的结果取决于 PATH 顺序

### sys.path 的导入路径模型

Python 模块导入可建模为**有序路径搜索**：

$$\text{import}(name) \iff \exists p \in sys.path: \exists file(name, p)$$

其中 $file(name, p)$ 表示在路径 $p$ 下存在 $name.py$、$name\backslash\_\_init\_\_.py$ 或 $name.so$（C 扩展）。

**sys.path 的标准顺序**（从左到右）：

| 序号 | 路径 | 含义 |
|------|------|------|
| 0 | 脚本目录或 `""`（交互式） | 优先查找用户脚本 |
| 1 | `$PYTHONPATH` 各目录 | 环境变量指定 |
| 2 | 安装依赖标准库目录 | stdlib |
| 3 | `$VIRTUAL_ENV/Lib/site-packages` | 虚拟环境第三方包 |
| 4 | 其他第三方 site-packages | |

### 虚拟环境隔离的形式化

虚拟环境的隔离效果可形式化为：

$$\forall pkg \in venv_A.\text{site-packages}: \text{import}(pkg) \Rightarrow venv_A.\text{namespace}$$
$$\forall pkg \in venv_B.\text{site-packages}: \text{import}(pkg) \Rightarrow venv_B.\text{namespace}$$

且：

$$\text{venv}_A.\text{site-packages} \cap \text{venv}_B.\text{site-packages} = \emptyset \quad \text{（隔离性）}$$

隔离的本质是 **sys.path 的有序优先**：

$$\text{import}(pkg) \iff \exists p \in \text{sys.path}: p = \text{venv}/Lib/site-packages \land pkg \in p$$

### pip 依赖解析的约束

pip 使用**贪婪版本匹配 + 回溯求解**策略：

$$\text{selected\_version}(pkg) = \max \{ v \in \text{available\_versions}(pkg) \mid v \succeq \text{constraint} \}$$

其中 $\succeq$ 是满足语义版本约束的偏序关系。

**依赖冲突的数学描述**：

$$\exists pkg_A, pkg_B: \text{constraint}(pkg_A) \cap \text{constraint}(pkg_B) = \emptyset$$

当冲突发生时，pip 尝试回溯：

$$\text{backtrack}(G, conflict) = \begin{cases} \text{重新选择} & \text{若存在未尝试分支} \\ \text{失败} & \text{若所有分支均尝试且失败} \end{cases}$$

**时间复杂度**：最坏情况指数级（依赖版本数指数爆炸），但实际中受版本数量限制，通常可解。

### PYTHONPATH 的导入隔离

PYTHONPATH 环境变量是一组由 OS 路径分隔符连接的目录列表：

$$PYTHONPATH = \bigcup_{i=1}^{n} path_i$$

**导入时的查找代价**：

$$\text{lookup}(name) = \sum_{p \in \text{sys.path}} \begin{cases} 1 & \text{若 } file(name, p) \text{ 存在} \\ 0 & \text{否则} \end{cases}$$

在 sys.path 靠前位置添加包含同名模块的路径会**遮蔽**后续路径中的同名模块。这与 `PATH` 的遮蔽原则一致。

## 数据流

### Python 安装的数据流

<pre>
安装包 (.exe/.pkg)           文件系统                环境变量
+-------------------+          +------------------+    +------------------+
| 解压标准库       | -------> | {prefix}/Lib/    |    | PATH += {prefix}|
| 复制 python.exe | -------> | {prefix}/Scripts/|    +------------------+
| 写入 pyvenv.cfg | -------> | pyvenv.cfg       |
+-------------------+          +------------------+

  {prefix} 由安装时选择:
  - Windows: C:\Users\{user}\AppData\Local\Programs\Python\Python312
  - Linux:   /usr/local/lib/python3.12
</pre>

**pip 安装的完整数据流**：

<pre>
pip install requests==2.28.0

Step 1: PyPI 查询
  HTTP GET https://pypi.org/pypi/requests/2.28.0/json
  返回: JSON {dependencies, files, hash}

Step 2: 依赖解析
  构建 DAG: requests → urllib3, charset-normalizer, ...
  贪心选择最高兼容版本
  回溯处理冲突

Step 3: 下载 wheel
  目的地: ~/.cache/pip/wheels/{hash}.whl
  验证 SHA256 hash

Step 4: 解压到 site-packages
  .whl 是 zip 格式 → 解压到 Lib/site-packages/
  创建 requests-2.28.0.dist-info/ (METADATA, RECORD, WHEEL)

Step 5: 缓验
  pip-selfcheck.json 记录已验证版本
</pre>

### 虚拟环境激活的数据流

<pre>
# Windows: myenv\Scripts\activate.bat
# Linux:  source myenv/bin/activate

激活前:
  PATH = /usr/local/bin:/usr/bin:...
  VIRTUAL_ENV = undefined
  sys.path = ['', /usr/local/lib/python3.12, ...]

激活后 (Windows):
  VIRTUAL_ENV = D:\path\to\myenv
  PATH = D:\path\to\myenv\Scripts:  <-- 插入头部
          /usr/local/bin:/usr/bin:...  (原始 PATH 追加)
  sys.path = [''] + [D:\path\to\myenv\Lib\site-packages] +
             [D:\path\to\myenv\Lib\stdlib] +
             [系统 site-packages 若 include-system-site-packages=true]

激活后 (Linux):
  PATH = /path/to/myenv/bin:  <-- 插入头部
         /usr/local/bin:...
  (deactivate 时恢复原 PATH，unset VIRTUAL_ENV)
</pre>

**venv 创建模式（symlink vs copy）**：

<pre>
python -m venv myenv --symlinks
         │
         ▼
   myenv/Scripts/python.exe ── symlink ──> 原始 python.exe
   myenv/Lib/ (不复制) ──────────────────> 原始 Lib（通过 pyvenv.cfg 的 home 指向）

python -m venv myenv --copies
         │
         ▼
   myenv/Scripts/python.exe ── copy ──> 原始 python.exe 副本
   myenv/Lib/ (不复制) ──────────────────> 同上（通过 home 指向原始 stdlib）
</pre>

### pip 缓存命中判定数据流

<pre>
pip install requests==2.28.0

查询阶段:
  1. 查 ~/.cache/pip/*.whl 是否有同名 hash 匹配
  2. 若命中 → 直接解压，跳过下载
  3. 若未命中 → 下载 wheel，写入缓存

缓存 Key 计算:
  hash = SHA256(wheel_filename + version + python_tag + abi_tag + platform_tag)
  命中条件: hash 精确匹配

缓存写入:
  ~/.cache/pip/wheels/{package}/{hash}.whl
  pip-selfcheck.json: {"installed": {pkg: (version, hash)}}
</pre>

**缓存命中率建模**：

$$P(\text{命中}) = \frac{|\{\text{已缓存且版本相同}\}|}{|\{\text{请求总数}\}"|}$$

当依赖树稳定（不频繁变更版本）时，缓存命中率接近 100%；当频繁变更需求时，缓存失效快。

## 机制

### 虚拟环境的三层隔离

虚拟环境通过**三层隔离**实现完全依赖隔离：

1. **解释器副本**：通过 symlink 或 copy 指向原始 Python 安装
2. **site-packages 隔离**：独立的第三方包目录，无系统包污染
3. **sys.path 调整**：虚拟环境的 site-packages 在 sys.path 靠前位置，优先于系统 site-packages

**关键约束**：`pyvenv.cfg` 中的 `home` 指向原始 Python 安装路径，解释器本身的 stdlib 来自原始安装，仅 site-packages 来自虚拟环境。这保证了：
- 虚拟环境不复制整个 Python 发行版（体积可控）
- 系统 Python 升级后，通过 symlink 的 venv 自动使用新版 Python

**pyvenv.cfg 配置**：

```ini
home = /usr/local/python3.12           # 原始 Python 安装路径
include-system-site-packages = false    # 是否包含系统 site-packages
version = 3.12.0                       # Python 版本号
```

`include-system-site-packages = true` 时，虚拟环境的 sys.path 会包含系统 site-packages，依赖冲突风险增加，不推荐生产环境使用。

### symlink 与 copy 的设计权衡

| 模式 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| `--symlinks` | 磁盘占用小；系统 Python 升级自动生效 | Windows 需开发者模式；跨卷符号链接复杂 | Linux/Mac 开发环境 |
| `--copies` | 隔离性强；不受系统 Python 影响 | 磁盘占用大；升级需重建 venv | Windows 生产环境 |

**Windows 默认行为**：Windows 10/11 上默认尝试 symlinks，若权限不允许则回退到 copies。Linux/Mac 始终使用 symlinks。

### pip 的包解析机制

pip 从 PyPI（默认）或镜像源下载包。三种分发格式：

| 格式 | 特点 | 安装速度 |
|------|------|----------|
| sdist (.tar.gz) | 源码分发，需构建 | 慢（含编译步骤） |
| wheel (.whl) | 预编译二进制 | 快（直接解压） |
| platform wheel | 平台特定（如 cp312-cp312-win_amd64） | 最快 |

**语义版本约束解析**：

| 约束符 | 语义 | 示例 |
|--------|------|------|
| `>=1.0,<2.0` | 兼容范围 | `requests>=2.28.0` |
| `~=1.4` | 兼容向上（`>=1.4,<2.0`） | `numpy~=1.24` |
| `==1.4.2` | 精确版本 | `django==5.0.1` |
| `!=1.4.*` | 版本排除 | `pytest!=7.0.0` |

**回溯算法的具体行为**：
1. 构建所有包的依赖图（所有版本组合）
2. 对每个包，从最高版本向下贪心选择第一个满足约束的版本
3. 若最终方案存在冲突（如 A 需要 `C>=2.0`，B 需要 `C<2.0`），pip 从冲突节点回溯
4. 回溯时尝试次优选择，直到找到兼容组合或确认无解

**冲突场景示例**：

```
package-a requires requests>=2.28.0
package-b requires requests<2.0.0
# 无兼容版本 → 报告冲突
```

### site-packages 的物理布局

<pre>
venv/ (虚拟环境根目录)
├── pyvenv.cfg               # 配置文件（home, version, 等等）
├── Scripts/                  # Windows: 可执行文件
│     ├── python.exe          # 解释器入口（symlink 或 copy）
│     ├── pip.exe             # pip 入口
│     └── activate           # 激活脚本
├── Lib/
│     ├── site-packages/      # 第三方包安装目录
│     │     ├── mypackage-1.2.3.dist-info/
│     │     │     ├── METADATA      # 包元数据（依赖声明、版本）
│     │     │     ├── RECORD        # 安装文件清单 + hash
│     │     │     └── WHEEL         # wheel 元信息
│     │     └── otherpkg-0.1.0.dist-info/
│     └── python3.12/         # 标准库（通过 home 链接，非复制）
└── include/                  # C 头文件（若需要编译 C 扩展）
</pre>

**dist-info 目录的作用**：`METADATA` 包含包的完整元信息（名称、版本、依赖列表、许可证等），pip 使用它进行依赖解析和卸载验证。`RECORD` 记录每个已安装文件及其 hash，用于完整性校验和卸载。

### 版本约束（Python 3.12 stable / Python 3.14 latest）

本目录底座为 `Python 3.12`，前沿为 `Python 3.14`。

$$底座 = Python\;3.12 \quad 前沿 = Python\;3.14 \quad 版本空间 = 底座 \cup 前沿$$

**约束**：Python 3.14 是前沿版本，可能存在不稳定因素。生产环境应使用 Python 3.12 稳定版。

- **Python 3.12（稳定底座）**：改进错误消息、`async` 协程改进、`typing` 增强
- **Python 3.14（前沿增量）**：实验性 `py	stdin` 模块（PEP 749），改进的 JIT 编译器接口

## 参考存根

```bash
# 查看 Python 和 pip 版本
python --version
pip --version

# 查看 sys.path（导入路径搜索顺序）
python -c "import sys; print(sys.path)"

# 查看已安装的包列表
pip list
pip freeze > requirements.txt

# 虚拟环境创建与激活
python -m venv myenv          # 创建
source myenv/bin/activate     # Linux/Mac 激活
myenv\Scripts\activate        # Windows 激活
deactivate                    # 退出虚拟环境

# pip 缓存管理
pip cache info               # 查看缓存信息
pip cache purge              # 清除缓存
```

---

**Python 3.14 增量特性**：实验性 `py	stdin` 模块（PEP 749）提供标准化标准流重定向接口。

**Python 3.14 重大变化**：无。
