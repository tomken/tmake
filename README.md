
# Tmake

Tmake 是一个用 python 包装 CMake 的跨平台构建脚本结合，易的方式管理 C++ 项目的依赖、构建、IDE 生成等。

### 一键安装

```curl git sh```

### 本地使用

**下载源码**

```clone https://github.com/tomken/tmake.git YourFolder```

**编写工程配置**

[模板](https://github.com/tomken/tmake.git) 

**示例构建 XCode 工程**

```YourFolder/tmake project xcode open```

### 命令
支持下面一些命令，具体请看 help 介绍
* ./tmake version
* ./tmake help
* ./tmake build
* ./tmake project
* ./tmake clean

### 支持的平台
* MacOS & iOS
* Windows
* Linux


