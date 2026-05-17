# Tombstone 日志格式说明

## 文档信息

| 字段 | 值 |
|------|-----|
| **版本** | v1.0 |
| **适用版本** | Android 8.0+ |
| **最后更新** | 2026-05-17 |
| **状态** | Draft |
| **标签** | android, tombstone, crash, native |

---

## 1. 概述

Tombstone 是 Android 系统记录原生崩溃（Native Crash）的日志文件，包含完整的堆栈跟踪、寄存器状态和内存映射信息。

---

## 2. Tombstone 日志格式

### 2.1 日志位置

Tombstone 文件位于：
- `/data/tombstones/tombstone_<n>` - 最多保存 10 个文件

### 2.2 标准格式结构

```text
*** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***
Build fingerprint: '<fingerprint>'
Revision: '<revision>'
ABI: '<abi>'
Timestamp: <timestamp>
pid: <pid>, tid: <tid>, name: <thread_name>  >>> <process_name> <<<
signal <signal> (SIG<signal_name>), code <code> (SI_<code>), fault addr <address>

Abort message: '<message>'

backtrace:
#00 pc <address> <library.so>:<offset>
#01 pc <address> <library.so>:<offset>
#02 pc <address> <library.so>:<offset>
...

libc base address: <address>

Stack frame #<frame>:
 PC: <address>
 SP: <address>
 LR: <address>
 ...

Memory mapping:
 <start>-<end> <permissions> <offset> <device> <inode> <name>
 ...
```

### 2.3 关键字段定义

| 字段 | 类型 | 含义 | 示例 |
|------|------|------|------|
| fingerprint | string | 构建指纹 | google/pixel5/pixel5:13/... |
| abi | string | 应用二进制接口 | arm64-v8a |
| pid | int | 进程ID | 1234 |
| tid | int | 线程ID | 1245 |
| signal | int | 信号编号 | 11 |
| signal_name | string | 信号名称 | SIGSEGV |
| fault_addr | string | 错误地址 | 0x00000000 |

### 2.4 常见信号类型

| 信号 | 名称 | 含义 | 常见原因 |
|------|------|------|----------|
| 6 | SIGABRT | 程序主动中止 | assert 失败 |
| 11 | SIGSEGV | 段错误 | 空指针、越界访问 |
| 8 | SIGFPE | 浮点异常 | 除零等 |
| 13 | SIGPIPE | 管道断开 | 写入已关闭的socket |
| 4 | SIGILL | 非法指令 | 指令错误、代码损坏 |

---

## 3. 解析方法

### 3.1 解析步骤

1. **识别信号类型**：查看 `signal` 字段
2. **定位错误地址**：查看 `fault addr`
3. **分析堆栈**：查看 `backtrace` 部分
4. **符号化**：使用 ndk-stack 或 addr2line 还原符号
5. **检查内存映射**：查看 `Memory mapping`

### 3.2 符号化工具

```bash
# 使用 ndk-stack
ndk-stack -sym <path_to_symbols> -dump <tombstone_file>

# 使用 addr2line
addr2line -f -e <library.so> <address>
```

---

## 4. 常见模式

### 4.1 崩溃根因模式

| 模式 | 信号 | 描述 | 根因 |
|------|------|------|------|
| 空指针解引用 | SIGSEGV | 访问 0x0 地址 | 未初始化指针 |
| 数组越界 | SIGSEGV | 访问超出边界 | 索引错误 |
| 堆溢出 | SIGSEGV | 堆内存越界 | 缓冲区溢出 |
| 栈溢出 | SIGSEGV | 栈空间耗尽 | 递归过深 |
| 断言失败 | SIGABRT | assert 失败 | 条件不满足 |

### 4.2 示例 Tombstone

```text
*** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***
Build fingerprint: 'google/pixel5/pixel5:13/TQ3A.230705.001/...'
ABI: 'arm64'
Timestamp: 2026-03-04 10:23:28.000000000+0800
pid: 1234, tid: 1245, name: RenderThread  >>> com.example.app <<<
signal 11 (SIGSEGV), code 1 (SEGV_MAPERR), fault addr 0x0000000000000000

Abort message: 'null pointer dereference'

backtrace:
#00 pc 0x0000000000012345  /system/lib64/libnative-lib.so:0x12345
#01 pc 0x0000000000023456  /system/lib64/libnative-lib.so:0x23456
...
```

---

## 5. 参考资料

- Android 官方文档: [Tombstones](https://source.android.com/docs/core/debug/tombstones)
- NDK 工具: [ndk-stack](https://developer.android.com/ndk/guides/ndk-stack)