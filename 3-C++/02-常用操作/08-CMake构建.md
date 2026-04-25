# CMake构建

**CMake是通过声明式配置描述构建产物与依赖关系的工具，通过生成器表达式将配置转化为各平台原生构建文件。**

## 核心概念

**Target是构建原子单元，通过target_*命令设置其属性，依赖传递由PUBLIC/PRIVATE/INTERFACE控制。**

<pre>
CMakeLists.txt → [cmake] → Makefile/Ninja项目文件
                      ↓
            target_link_libraries()
</pre>

### 最小项目

```cmake
cmake_minimum_required(VERSION 3.16)
project(MyProject VERSION 1.0 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
aux_source_directory(src SRCS)
add_executable(myapp ${SRCS})
```

## Target属性

**target_include_directories设置包含路径，target_link_libraries设置链接库，PUBLIC/PRIVATE/INTERFACE决定传递性。**

```cmake
target_include_directories(mylib PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_link_libraries(app PRIVATE mylib)
```

### 传递性说明

| 说明符 | 当前目标 | 依赖此目标的其他目标 |
|--------|---------|-------------------|
| PRIVATE | 使用 | 不继承 |
| PUBLIC | 使用 | 继承 |
| INTERFACE | 不使用 | 继承 |

## find_package

**find_package通过模块模式或配置模式查找库，生成导入目标供target_link_libraries使用。**

```cmake
find_package(Threads REQUIRED)
find_package(Boost 1.70 REQUIRED COMPONENTS filesystem)
target_link_libraries(myapp PRIVATE Threads::Threads Boost::filesystem)
```

## 生成器表达式

**生成器表达式$<CONFIG:Debug>在构建时根据配置动态替换，是条件编译选项的标准写法。**

```cmake
target_link_libraries(myapp PRIVATE
    $<$<CONFIG:Debug>:debug_lib>
    $<$<CONFIG:Release>:release_lib>
)
```

## 构建流程

```bash
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
```
