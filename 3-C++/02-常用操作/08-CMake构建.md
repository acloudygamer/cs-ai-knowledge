# CMake 构建

CMake 是 C++ 项目最流行的跨平台构建系统，通过 `CMakeLists.txt` 描述构建过程。

## 基础语法

### 最小项目

```cmake
cmake_minimum_required(VERSION 3.16)
project(MyProject VERSION 1.0 LANGUAGES CXX)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 查找源文件
aux_source_directory(src SRCS)

# 生成可执行文件
add_executable(myapp ${SRCS})

# 链接库
target_link_libraries(myapp PRIVATE some_library)
```

### 目录结构示例

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

```cmake
# 可执行文件
add_executable(myapp main.cpp)

# 静态库
add_library(mylib STATIC utils.cpp math.cpp)

# 共享库
add_library(myshd SHARED utils.cpp)
```

### 目标属性

```cmake
add_executable(myapp main.cpp)

# 包含目录
target_include_directories(myapp PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# 链接库
target_link_libraries(myapp PRIVATE
    pthread
    stdc++fs
)

# 编译选项
target_compile_options(myapp PRIVATE
    -Wall
    -Wextra
    -O2
)

# C++ 标准
target_compile_features(myapp PUBLIC cxx_std_20)
```

### PUBLIC / PRIVATE / INTERFACE

- **PRIVATE**：仅当前目标使用
- **PUBLIC**：当前目标和依赖此目标的其他目标都使用
- **INTERFACE**：仅依赖此目标的其他目标使用

```cmake
# mylib 的 include 目录传递给你app
target_link_libraries(myapp PUBLIC mylib)
```

## 查找包（find_package）

### 查找系统库

```cmake
# 查找 Boost
find_package(Boost 1.70 REQUIRED COMPONENTS filesystem system)

# 查找 OpenCV
find_package(OpenCV REQUIRED)

# 查找 Eigen
find_package(Eigen3 REQUIRED)

# 使用找到的包
add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE
    Boost::filesystem
    ${OpenCV_LIBS}
    Eigen3::Eigen
)
```

### 查找自定义模块

```cmake
# 添加模块搜索路径
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

find_package(MyLibrary REQUIRED)
target_link_libraries(myapp PRIVATE MyLibrary::MyLibrary)
```

## 条件构建

### 平台判断

```cmake
if(WIN32)
    # Windows 特定配置
    target_compile_definitions(myapp PRIVATE _WIN32_WINNT=0x0A00)
elseif(UNIX AND NOT APPLE)
    # Linux 特定配置
    target_compile_options(myapp PRIVATE -Wall)
endif()

# Apple 特殊处理
if(APPLE)
    target_link_libraries(myapp PRIVATE "-framework CoreFoundation")
endif()
```

### 选项开关

```cmake
option(BUILD_TESTS "Build test suite" ON)
option(ENABLE_WARNINGS "Enable compiler warnings" ON)

if(ENABLE_WARNINGS)
    if(MSVC)
        target_compile_options(myapp PRIVATE /W4)
    else()
        target_compile_options(myapp PRIVATE -Wall -Wextra)
    endif()
endif()
```

## 子目录与依赖

### 添加子目录

```cmake
# src/CMakeLists.txt
add_library(mylib STATIC utils.cpp)
target_include_directories(mylib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/../include)

# tests/CMakeLists.txt
find_package(GTest)
add_executable(tests test_main.cpp test_utils.cpp)
target_link_libraries(tests PRIVATE
    GTest::gtest
    GTest::gtest_main
    mylib  # 自动找到库的 include
)
```

### 依赖外部项目

```cmake
# FetchContent（CMake 3.24+）
include(FetchContent)

FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)

FetchContent_MakeAvailable(googletest)

# 旧版 CMake（3.24 之前）
include(ExternalProject)
ExternalProject_Add(googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG release-1.12.0
    SOURCE_DIR ${CMAKE_BINARY_DIR}/googletest-src
    BINARY_DIR ${CMAKE_BINARY_DIR}/googletest-build
    CMAKE_ARGS -DCMAKE_INSTALL_PREFIX=${CMAKE_BINARY_DIR}/install
    INSTALL_COMMAND ""
)
```

## 安装与导出

### 安装规则

```cmake
install(TARGETS myapp
    RUNTIME DESTINATION bin
)

install(TARGETS mylib
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    PUBLIC_HEADER DESTINATION include
)

install(FILES config.h DESTINATION include)
```

### 导出目标

```cmake
# 安装时导出
install(EXPORT myTargets
    FILE MyTargets.cmake
    NAMESPACE MyLib::
    DESTINATION lib/cmake/MyLib
)

# 创建可重用的包配置
include(CMakePackageConfigHelpers)

configure_package_config_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/MyLibConfig.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/MyLibConfig.cmake
    INSTALL_DESTINATION lib/cmake/MyLib
)

install(FILES ${CMAKE_CURRENT_BINARY_DIR}/MyLibConfig.cmake
    DESTINATION lib/cmake/MyLib
)
```

## 测试集成

### CTest

```cmake
enable_testing()

add_test(NAME mytest COMMAND mytest_executable)

# 自定义测试
add_test(NAME mytest COMMAND python ${CMAKE_CURRENT_SOURCE_DIR}/run_test.py)

# 测试驱动
include(GoogleTest)
gtest_discover_tests(tests)
```

## 常用变量

| 变量 | 说明 |
|------|------|
| `CMAKE_SOURCE_DIR` | 源码根目录 |
| `CMAKE_BINARY_DIR` | 构建根目录 |
| `CMAKE_CURRENT_SOURCE_DIR` | 当前 CMakeLists.txt 所在目录 |
| `CMAKE_CURRENT_BINARY_DIR` | 当前构建目录 |
| `CMAKE_CXX_STANDARD` | C++ 标准版本 |
| `CMAKE_BUILD_TYPE` | 构建类型（Debug/Release） |
| `CMAKE_PREFIX_PATH` | 包搜索路径 |

## 构建类型

```cmake
# 设置默认构建类型
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release)
endif()

# 为特定构建类型设置标志
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG")

# CMake Presets（CMake 3.21+）
# CMakePresets.json
{
    "version": 4,
    "configurePresets": [
        {
            "name": "release",
            "binaryDir": "${sourceDir}/build",
            "cacheVariables": {
                "CMAKE_BUILD_TYPE": "Release",
                "ENABLE_WARNINGS": "ON"
            }
        }
    ]
}
```

## 完整示例

```cmake
cmake_minimum_required(VERSION 3.16)
project(MyApp VERSION 1.0.0 LANGUAGES CXX)

# C++ 标准
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 构建设置
option(BUILD_TESTS "Build test suite" ON)
option(ENABLE_WARNINGS "Enable warnings" ON)

# 调试/发布
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    add_compile_definitions(DEBUG_MODE)
endif()

# 查找包
find_package(Boost 1.70 REQUIRED COMPONENTS filesystem)

# 可执行文件
add_executable(myapp src/main.cpp)

# 链接
target_link_libraries(myapp PRIVATE
    Boost::filesystem
)

# 测试
if(BUILD_TESTS)
    find_package(GTest)
    add_subdirectory(tests)
endif()

# 安装
install(TARGETS myapp RUNTIME DESTINATION bin)
install(DIRECTORY config/ DESTINATION etc/myapp)
```
