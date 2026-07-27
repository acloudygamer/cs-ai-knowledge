# CMake 构建

## 定义

CMake 是**声明式构建配置语言**，通过 `CMakeLists.txt` 描述构建产物的图依赖关系，经生成器（Makefile、Ninja、Visual Studio 等）转换为目标平台的原生构建指令。其本质是将**构建意图（Target + Dependency Graph）**与**构建执行（Build System）**解耦。

## 数学模型

**构建依赖图**：

构建系统本质上是一个 **DAG（有向无环图）**。设节点集合 $T$ 为 Target，边集合 $E \subseteq T \times T$ 表示依赖关系（ $(A, B) \in E$ 表示 A 依赖 B，即 B 必须先于 A 构建）。 为 Target，边集合 $E \subseteq T \times T$ 表示依赖关系（ $(A, B) \in E$ 表示 A 依赖 B，即 B 必须先于 A 构建）。 表示依赖关系（ $(A, B) \in E$ 表示 A 依赖 B，即 B 必须先于 A 构建）。 表示 A 依赖 B，即 B 必须先于 A 构建）。

**拓扑排序约束**：
 $\forall (A, B) \in E: \text{build-order}(B) < \text{build-order}(A)$ 

CMake 通过 `add_dependencies`、`target_link_libraries` 等命令向图中插入节点和边。

**DAG 的形式化性质**：

| 性质 | 描述 | 在 CMake 中的意义 |
|------|------|------------------|
| 无环性 | $\nexists (A, B) \in E^+: (A, A) \in E$ | 禁止循环依赖 | | 禁止循环依赖 |
| 传递性 | $(A, B) \in E \land (B, C) \in E \Rightarrow (A, C) \in E$ | 间接依赖成立 | | 间接依赖成立 |
| 偏序性 | 非所有节点对都可比较 | 允许并行构建 |

**拓扑排序算法**：

Kahn 算法：
```
L = []  // 拓扑序
S = {入度为0的节点}
while S 非空:
    n = S.pop()
    L.append(n)
    for each m in n的后继:
        删除边 n→m
        if m.入度 == 0: S.add(m)
if 仍有边剩余: 报告循环依赖
```

**生成器表达式的条件求值**：

生成器表达式是配置感知的字符串模板，形式化为：
 $E = \$ \langle \text{<}type\text{:}cond\text{>}:value\rangle$ 

**求值函数**：
 $\text{eval}(E, C) = \begin{cases} value & \text{if } \text{cond} \in C \\ \text{empty} & \text{otherwise} \end{cases}$ 

其中 $C$ 是配置集合（`Debug`, `Release`, `RelWithDebInfo` 等）。多条件链式展开： 是配置集合（`Debug`, `Release`, `RelWithDebInfo` 等）。多条件链式展开：
 $\text{eval}(\$ <CONFIG:Debug>: $ `debug_lib` $, \{Debug\}) =$ `"debug_lib"` 

**生成器表达式的完备性**：

设配置集合 $C = \{c_1, c_2, ..., c_n\}$。生成器表达式可构造如下逻辑： 。生成器表达式可构造如下逻辑：

| 表达式 | 语义 |
|--------|------|
| $\$ <CONFIG:Debug>:X$ | Debug 配置下为 X，否则为空 | | Debug 配置下为 X，否则为空 |
| $\$ <NOT: $ <CONFIG:Debug>>:X$ | 非 Debug 下为 X |<CONFIG:Debug>>:X$ | 非 Debug 下为 X |
| $\$ <AND: $ <CONFIG:Debug>,$ <CONFIG:Release>>:X $ | 同时满足时为 X（无意义，永空） |<CONFIG:Debug>, $ <CONFIG:Release>>:X$ | 同时满足时为 X（无意义，永空） | | 同时满足时为 X（无意义，永空） |
| $\$ <OR: $ <CONFIG:Debug>,$ <CONFIG:Release>>:X $ | 任一满足时为 X |<CONFIG:Debug>, $ <CONFIG:Release>>:X$ | 任一满足时为 X | | 任一满足时为 X |

**PUBLIC/PRIVATE/INTERFACE 依赖传递**：

设 $D_T$ 为 Target $T$ 的直接依赖集， $P_T$ 为传播依赖集（影响其他 Target 的）。 为 Target $T$ 的直接依赖集， $P_T$ 为传播依赖集（影响其他 Target 的）。 的直接依赖集， $P_T$ 为传播依赖集（影响其他 Target 的）。 为传播依赖集（影响其他 Target 的）。

| 传递性 | 含义 | 公式 |
|--------|------|------|
| PRIVATE | 仅当前 Target 使用，不传播 | $P_T = D_T \cap \text{used-by}(T)$ | |
| PUBLIC | 当前 Target 使用，且传播 | $P_T = D_T$ | |
| INTERFACE | 仅传播，不直接使用 | $P_T = D_T$ | |

**传播的图论模型**：

依赖传播等价于在 DAG 上做**广度优先传播（BFS）**：

```cpp
// 伪代码：属性传播
void propagate(Target t) {
    queue q = {t};
    while (!q.empty()) {
        Target cur = q.pop();
        for (Target nxt : cur.public_deps()) {
            nxt.inherit_props(cur);
            q.push(nxt);
        }
    }
}
```

传播的属性包括：`include_directories`、`compile_options`、`link_libraries`、`compile_definitions`。

## 数据流

<pre>
CMakeLists.txt
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  配置阶段（Configure Step）                                   │
│  1. CMakeLists.txt 解析（AST 构建）                          │
│  2. find_package 查找依赖（模块/配置模式）                     │
│  3. 变量求值与生成器表达式展开                                 │
│  4. Target 图构建（add_executable, add_library 等）           │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
[Cache] CMakeCache.txt（配置变量持久化）
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  生成阶段（Generate Step）                                    │
│  1. 拓扑排序确定构建顺序                                      │
│  2. 生成器根据 Target 图生成原生构建文件                       │
│     - Makefile（Ninja 兼容）                                  │
│     - Ninja build.ninja                                       │
│     - Visual Studio .sln/.vcxproj                             │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
原生构建文件（Makefile / build.ninja）
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  构建阶段（Build Step）                                       │
│  编译器调用：cmake --build . --config Release                 │
│  链接器调用：ld / link                                        │
└─────────────────────────────────────────────────────────────┘
</pre>

**所有权流转**：

- **CMakeLists.txt** 声明 Target 所有权（`add_library`/`add_executable`）
- **依赖信息**通过 `target_link_libraries` 转移链接权
- **构建产物**（`.a`, `.so`, `.exe`）由原生构建系统管理

**配置变量与缓存机制**：

CMakeCache.txt 实现了两阶段求值的持久化：
- **第一阶段**（Configure）：变量求值，结果写入缓存
- **第二阶段**（Build）：读取缓存，生成构建指令

缓存变量类型：
| 类型 | 修辞符 | 说明 |
|------|--------|------|
| 字符串 | 无 | 直接存储 |
| 路径 | PATH | 路径分隔符转换 |
| 布尔 | BOOL | ON/OFF/TRUE/FALSE |
| 文件路径 | FILEPATH | 存在性检查 |
| 目录路径 | DIRPATH | 存在性检查 |

## 机制

**find_package 两种模式**：

**模块模式**（Module Mode）：CMake 搜索 `${CMAKE_MODULE_PATH}/FindXXX.cmake`。若找到，执行该模块，模块负责设置 `XXX_FOUND` 及相关变量。典型用于纯头文件库或支持 CMake 的现代库。

**配置模式**（Config Mode）：CMake 搜索 `${XXX}_DIR` 或默认路径下的 `lib/cmake/XXX/` 或 `XXXConfig.cmake`。配置文件由库提供者编写，声明 `XXX_Target` 导入目标（CMake 3.x+ 推荐方式）。

```cmake
# 模块模式
find_package(Threads REQUIRED)  # FindThreads.cmake

# 配置模式
find_package(Boost 1.70 REQUIRED COMPONENTS filesystem)
# → 查找 BoostConfig.cmake
```

**find_package 搜索路径的形式化**：

设搜索根目录集合 $R$，包名为 $P$。模块模式搜索： ，包名为 $P$。模块模式搜索： 。模块模式搜索：
 $S_{\text{module}} = \{ p \in R \mid \exists \text{ Find}P\text{.cmake} \}$ 

配置模式搜索：
 $S_{\text{config}} = \{ p \in R \mid \exists P\text{Config.cmake} \lor \exists p/P\text{Config.cmake} \}$ 

**target_* 命令的属性传播**：

`target_include_directories`、`target_compile_options`、`target_link_libraries` 等命令设置 Target 属性。这些属性通过传递性说明符影响依赖图：

```cmake
add_library(mylib INTERFACE)          # INTERFACE library（无构建产物）
target_include_directories(mylib INTERFACE ${CMAKE_SOURCE_DIR}/include)
# mylib 的消费者自动继承 include 路径

add_executable(app PRIVATE mylib)
# app 获得 mylib 的 INTERFACE 属性（include 路径）
# 但 mylib 的实现不参与 app 的编译
```

**编译特性检测 vs 包管理**：

| 方式 | 检测对象 | 典型命令 |
|------|---------|---------|
| `find_package` | 外部依赖 | 第三方库 |
| `target_compile_features` | 编译器能力 | C++20/23 特性 |
| `check_include_file` | 系统头文件 | 平台差异 |
| `check_symbol_exists` | 库符号 | 系统调用 |

**CMake 作为图遍历问题**：

CMake 的本质是**依赖图的拓扑排序 + 属性传播**。构建过程可抽象为：

1. **图构建阶段**：解析 `CMakeLists.txt`，构建 Target DAG
2. **拓扑排序阶段**：确定构建顺序（Kahn 算法或 DFS 后序）
3. **属性传播阶段**：`target_link_libraries` 的传递性在 DAG 上做广度优先传播
4. **生成阶段**：按拓扑序为每个 Target 生成构建规则

关键操作：
 $P_T^{\text{PUBLIC}} = \bigcup_{B \in D_T^{\text{PUBLIC}}} P_B^{\text{PUBLIC}} \cup D_T^{\text{PUBLIC}}$ 

即 PUBLIC 依赖的传递闭包。

**约束条件与违反后果**：

- **循环依赖**：Target 图必须为 DAG。若 `A` 依赖 `B` 且 `B` 依赖 `A`，CMake 报错 `"Target contains cycle"`。
- **PRIVATE/PUBLIC/INTERFACE 混用错误**：若 `add_library(mylib STATIC)` 声明 PRIVATE 依赖，但消费者期望 PUBLIC，会导致链接错误（未定义符号）。
- **生成器表达式求值时机**：生成器表达式在**生成阶段**求值，而非配置阶段。这意味着 `if(CMAKE_BUILD_TYPE STREQUAL "Debug")` 是错误的——应该用生成器表达式 `$<CONFIG:Debug>:value`。

**CMake 的图论视角**：

```
Target DAG 示例：

app (exe)
 ├── mylib (static) ← PRIVATE deps: libA
 └── mylib_header (interface) ← INTERFACE deps: libB

构建顺序（拓扑序）：
1. libB（无依赖，最先构建）
2. libA（依赖 libB）
3. mylib_header（依赖 libB）
4. mylib（依赖 libA, mylib_header）
5. app（依赖 mylib, mylib_header）
```

## 参考存根

```cmake
cmake_minimum_required(VERSION 3.20)
project(MyApp VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(mylib STATIC src/lib.cpp)
target_include_directories(mylib PUBLIC ${CMAKE_SOURCE_DIR}/include)

add_executable(app src/main.cpp)
target_link_libraries(app PRIVATE mylib)
target_link_options(app PRIVATE $<$ <CONFIG:Debug>:-fsanitize=address>)<CONFIG:Debug>:-fsanitize=address>)
#                                                        ↑ 缺失的闭合 > 已修正

find_package(Threads REQUIRED)
target_link_libraries(app PRIVATE Threads::Threads)
```
