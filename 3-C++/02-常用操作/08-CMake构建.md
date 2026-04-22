# CMake 构建

C++ 项目需要跨平台构建，直接调用编译器处理大量源文件和依赖关系繁琐。CMake 通过 `CMakeLists.txt` 描述构建过程，生成各平台的原生构建文件。

## 核心概念

**目标（Target）** 是构建的基本单元：可执行文件、静态库、共享库。`target_*` 命令设置目标的属性：包含目录、链接库、编译选项。`PUBLIC`/`PRIVATE`/`INTERFACE` 控制依赖的传递性。`find_package` 查找系统库或第三方库。

## 基础语法

### 最小项目

CMakeLists.txt 基本结构：设置最低版本、定义项目、设置 C++ 标准、查找源文件、生成可执行文件。

### 参考样例

```cmake
cmake_minimum_required(VERSION 3.16)
project(MyProject VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

aux_source_directory(src SRCS)
add_executable(myapp ${SRCS})
target_link_libraries(myapp PRIVATE some_library)
```

### 目录结构

```
project/
├── CMakeLists.txt          # 根目录构建配置
├── src/
│   ├── CMakeLists.txt      # src 子目录
│   ├── main.cpp
│   └── utils.cpp
├── include/
│   └── utils.h
└── tests/
    └── CMakeLists.txt      # 测试目录
```

## 目标（Target）概念

### 源文件目标

### 参考样例

```cmake
# 可执行文件
add_executable(myapp main.cpp)

# 静态库
add_library(mylib STATIC utils.cpp math.cpp)

# 共享库
add_library(myshd SHARED utils.cpp)
```

### 目标属性

`target_include_directories` 设置包含目录，`target_link_libraries` 链接库，`target_compile_options` 设置编译选项，`target_compile_features` 设置 C++ 标准特性。

### 参考样例

```cmake
add_executable(myapp main.cpp)

target_include_directories(myapp PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(myapp PRIVATE
    pthread
    stdc++fs
)

target_compile_options(myapp PRIVATE
    -Wall
    -Wextra
    -O2
)

target_compile_features(myapp PUBLIC cxx_std_20)
```

### PUBLIC / PRIVATE / INTERFACE

依赖传递性：
- **PRIVATE**：仅当前目标使用
- **PUBLIC**：当前目标和依赖此目标的其他目标都使用
- **INTERFACE**：仅依赖此目标的其他目标使用

### 参考样例

```cmake
# mylib 的 include 目录传递给 app
target_include_directories(mylib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_link_libraries(app PRIVATE mylib)  # app 自动获得 mylib 的 include

# 仅 mylib 的依赖者使用，不影响 mylib 本身
target_include_directories(mylib INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/include)
```

## 查找包

`find_package` 查找系统库或第三方库，生成导入目标或提供变量。

### 参考样例

```cmake
# 查找包
find_package(Threads REQUIRED)
find_package(Boost 1.70 REQUIRED COMPONENTS filesystem system)

# 使用包
target_link_libraries(myapp PRIVATE Threads::Threads)
target_link_libraries(myapp PRIVATE Boost::filesystem)
```

## 子目录与模块化

使用 `add_subdirectory` 添加子目录，子目录应有自己的 CMakeLists.txt。

### 参考样例

```cmake
# 主 CMakeLists.txt
add_subdirectory(src)
add_subdirectory(tests)

# src/CMakeLists.txt
add_library(mylib STATIC utils.cpp math.cpp)
target_include_directories(mylib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/../include)
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `cmake_minimum_required()` | 最低 CMake 版本 |
| `project()` | 项目名称和语言 |
| `add_executable()` | 添加可执行目标 |
| `add_library()` | 添加库目标 |
| `add_subdirectory()` | 添加子目录 |
| `target_include_directories()` | 包含目录 |
| `target_link_libraries()` | 链接库 |
| `target_compile_options()` | 编译选项 |
| `target_compile_features()` | C++ 特性 |
| `find_package()` | 查找包 |
| `find_library()` | 查找库文件 |
| `configure_file()` | 复制文件并替换变量 |

## 生成器表达式

生成器表达式在构建时动态计算，适用于配置依赖路径、条件编译选项等。

### 参考样例

```cmake
# 条件链接库
target_link_libraries(myapp PRIVATE
    $<$<CONFIG:Debug>:debug_lib>
    $<$<CONFIG:Release>:optimized_lib>
)

# 条件包含目录
target_include_directories(myapp PRIVATE
    $<$<CONFIG:Debug>:${CMAKE_SOURCE_DIR}/debug_include>
)
```

## 构建步骤

### 参考样例

```bash
# 配置项目（生成构建文件）
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release

# 编译
cmake --build . --config Release

# 或者直接 make
make
```

## 完整示例

### 参考样例

```cmake
# CMakeLists.txt
cmake_minimum_required(VERSION 3.16)
project(MyApp VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 查找包
find_package(Threads REQUIRED)
find_package(Boost 1.70 REQUIRED COMPONENTS filesystem)

# 添加子目录
add_subdirectory(src)
add_subdirectory(tests)

# 配置安装
install(TARGETS myapp DESTINATION bin)
install(DIRECTORY include/ DESTINATION include)
```
