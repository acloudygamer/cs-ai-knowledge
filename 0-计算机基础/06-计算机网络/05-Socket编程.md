# Socket编程

## 概念

Socket是应用程序与网络协议栈之间的接口，封装了TCP/UDP的复杂操作。

```
┌─────────────────────────────────────────────────────────────┐
│                      Socket 编程模型                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  应用程序                                                    │
│    │                                                        │
│    ▼                                                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Socket API                              │   │
│  │   socket() → bind() → listen() → accept()            │   │
│  │   connect() → read()/write() → close()               │   │
│  └──────────────────────────────────────────────────────┘   │
│    │                                                        │
│    ▼                                                        │
│  TCP/IP协议栈 (内核)                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 关系

**关键连接**：
- Socket → **TCP**：面向连接的socket使用SOCK_STREAM
- Socket → **UDP**：无连接的socket使用SOCK_DGRAM
- 服务器socket → **端口**：bind()绑定到特定端口
- 客户端socket → **服务器**：connect()建立连接

## Socket类型

```python
# 主要Socket类型
socket_types = {
    "SOCK_STREAM": {
        "协议": "TCP",
        "特性": "面向连接、可靠、字节流",
        "应用": "HTTP、SSH、邮件"
    },
    "SOCK_DGRAM": {
        "协议": "UDP",
        "特性": "无连接、不可靠、数据报",
        "应用": "DNS、视频流"
    },
    "SOCK_RAW": {
        "协议": "原始套接字",
        "特性": "直接访问IP层，可自定义协议",
        "应用": "ping、traceroute"
    }
}
```

## TCP Socket编程

### TCP服务器流程

```
┌─────────────────────────────────────────────────────────────┐
│                    TCP 服务器 socket流程                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. socket()      创建socket                                │
│  2. bind()        绑定端口                                  │
│  3. listen()      监听连接                                  │
│  4. accept()      接受连接                                  │
│  5. read()/write() 数据交互                                 │
│  6. close()       关闭连接                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### TCP客户端流程

```
┌─────────────────────────────────────────────────────────────┐
│                    TCP 客户端 socket流程                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. socket()      创建socket                                │
│  2. connect()     连接服务器                                │
│  3. write()/read() 数据交互                                │
│  4. close()       关闭连接                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Go语言实现

```go
// TCP 服务端
package main

import (
    "bufio"
    "fmt"
    "net"
    "time"
)

func handleConnection(conn net.Conn) {
    defer conn.Close()
    addr := conn.RemoteAddr().String()
    fmt.Printf("[%s] 客户端连接\n", addr)

    reader := bufio.NewReader(conn)
    for {
        // 设置读超时
        conn.SetReadDeadline(time.Now().Add(60 * time.Second))

        message, err := reader.ReadString('\n')
        if err != nil {
            fmt.Printf("[%s] 客户端断开: %v\n", addr, err)
            return
        }

        // 处理消息
        message = message[:len(message)-1] // 去掉换行符
        fmt.Printf("[%s] 收到: %s\n", addr, message)

        // 发送响应
        response := fmt.Sprintf("收到: %s\n", message)
        conn.Write([]byte(response))
    }
}

func main() {
    listener, err := net.Listen("tcp", ":8080")
    if err != nil {
        fmt.Printf("监听失败: %v\n", err)
        return
    }
    defer listener.Close()

    fmt.Println("TCP服务器启动，监听 :8080")

    for {
        conn, err := listener.Accept()
        if err != nil {
            fmt.Printf("接受连接失败: %v\n", err)
            continue
        }

        // 启动 goroutine 处理连接
        go handleConnection(conn)
    }
}
```

```go
// TCP 客户端
package main

import (
    "bufio"
    "fmt"
    "net"
    "os"
    "time"
)

func main() {
    // 连接服务器
    conn, err := net.DialTimeout("tcp", "localhost:8080", 5*time.Second)
    if err != nil {
        fmt.Printf("连接服务器失败: %v\n", err)
        return
    }
    defer conn.Close()

    fmt.Println("已连接到服务器")

    // 启动 goroutine 读取服务器响应
    go func() {
        reader := bufio.NewReader(conn)
        for {
            message, err := reader.ReadString('\n')
            if err != nil {
                fmt.Printf("读取响应失败: %v\n", err)
                return
            }
            fmt.Print("服务器: ", message)
        }
    }()

    // 从 stdin 读取并发送
    scanner := bufio.NewScanner(os.Stdin)
    for scanner.Scan() {
        message := scanner.Text() + "\n"
        _, err := conn.Write([]byte(message))
        if err != nil {
            fmt.Printf("发送消息失败: %v\n", err)
            return
        }
    }
}
```

### Python实现

```python
# TCP 服务端
import socket
import threading

def handle_client(conn, addr):
    print(f"[{addr}] 客户端连接")
    try:
        while True:
            # 设置超时
            conn.settimeout(60)

            # 接收数据
            data = conn.recv(1024)
            if not data:
                break

            message = data.decode().strip()
            print(f"[{addr}] 收到: {message}")

            # 发送响应
            response = f"收到: {message}\n"
            conn.sendall(response.encode())

    except socket.timeout:
        print(f"[{addr}] 连接超时")
    except Exception as e:
        print(f"[{addr}] 错误: {e}")
    finally:
        conn.close()
        print(f"[{addr}] 连接关闭")

def main():
    # 创建 socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 绑定地址
    server.bind(('0.0.0.0', 8080))

    # 监听
    server.listen(5)
    print("TCP服务器启动，监听 :8080")

    try:
        while True:
            # 接受连接
            conn, addr = server.accept()
            # 启动线程处理
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
    except KeyboardInterrupt:
        print("\n服务器关闭")
    finally:
        server.close()

if __name__ == "__main__":
    main()
```

```python
# TCP 客户端
import socket
import threading
import sys

def receive_messages(sock):
    """接收服务器消息"""
    try:
        while True:
            data = sock.recv(1024)
            if not data:
                print("\n服务器断开连接")
                break
            print(f"\r服务器: {data.decode().strip()}\n> ", end="")
    except Exception as e:
        print(f"\n接收错误: {e}")

def main():
    # 连接服务器
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('localhost', 8080))
        print("已连接到服务器")
    except Exception as e:
        print(f"连接失败: {e}")
        return

    # 启动接收线程
    recv_thread = threading.Thread(target=receive_messages, args=(sock,))
    recv_thread.daemon = True
    recv_thread.start()

    # 发送消息
    try:
        while True:
            message = input("> ")
            if message.lower() in ('exit', 'quit'):
                break
            sock.sendall((message + "\n").encode())
    except KeyboardInterrupt:
        print("\n退出")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
```

### C语言 TCP服务器/客户端

```c
// TCP服务器
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define PORT 8080
#define BUFFER_SIZE 1024

int main() {
    int server_fd, client_fd;
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_len;
    char buffer[BUFFER_SIZE];
    int opt = 1;

    // 1. 创建socket
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    // 2. 绑定地址
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);
    bind(server_fd, (struct sockaddr*)&server_addr, sizeof(server_addr));

    // 3. 监听
    listen(server_fd, 5);
    printf("Server listening on port %d\n", PORT);

    // 4. 接受连接
    client_len = sizeof(client_addr);
    client_fd = accept(server_fd, (struct sockaddr*)&client_addr, &client_len);
    printf("Client connected from %s:%d\n",
           inet_ntoa(client_addr.sin_addr),
           ntohs(client_addr.sin_port));

    // 5. 数据交互
    while (1) {
        memset(buffer, 0, BUFFER_SIZE);
        int n = read(client_fd, buffer, BUFFER_SIZE - 1);
        if (n <= 0) break;
        printf("Received: %s", buffer);
        write(client_fd, buffer, n);  // 回显
    }

    close(client_fd);
    close(server_fd);
    return 0;
}
```

```c
// TCP客户端
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define PORT 8080
#define BUFFER_SIZE 1024

int main() {
    int sock_fd;
    struct sockaddr_in server_addr;
    char buffer[BUFFER_SIZE];

    // 1. 创建socket
    sock_fd = socket(AF_INET, SOCK_STREAM, 0);

    // 2. 连接服务器
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    inet_pton(AF_INET, "127.0.0.1", &server_addr.sin_addr);
    connect(sock_fd, (struct sockaddr*)&server_addr, sizeof(server_addr));

    printf("Connected to server\n");

    // 3. 数据交互
    while (1) {
        printf("Enter message: ");
        fgets(buffer, BUFFER_SIZE, stdin);
        write(sock_fd, buffer, strlen(buffer));

        memset(buffer, 0, BUFFER_SIZE);
        int n = read(sock_fd, buffer, BUFFER_SIZE - 1);
        if (n <= 0) break;
        printf("Received: %s", buffer);
    }

    close(sock_fd);
    return 0;
}
```

## UDP Socket编程

### Go语言实现

```go
// UDP 服务端
package main

import (
    "fmt"
    "net"
)

func main() {
    // 创建 UDP 地址
    addr, err := net.ResolveUDPAddr("udp", ":8080")
    if err != nil {
        fmt.Printf("地址解析失败: %v\n", err)
        return
    }

    // 监听
    conn, err := net.ListenUDP("udp", addr)
    if err != nil {
        fmt.Printf("监听失败: %v\n", err)
        return
    }
    defer conn.Close()

    fmt.Println("UDP服务器启动，监听 :8080")

    buffer := make([]byte, 1024)
    for {
        // 读取数据
        n, clientAddr, err := conn.ReadFromUDP(buffer)
        if err != nil {
            fmt.Printf("读取失败: %v\n", err)
            continue
        }

        message := string(buffer[:n])
        fmt.Printf("[%s] 收到: %s\n", clientAddr, message)

        // 发送响应
        response := fmt.Sprintf("收到: %s", message)
        conn.WriteToUDP([]byte(response), clientAddr)
    }
}
```

```go
// UDP 客户端
package main

import (
    "fmt"
    "net"
    "time"
)

func main() {
    // 连接服务器（UDP无需握手，但net.DialUDP会建立UDP连接）
    addr, err := net.ResolveUDPAddr("udp", "localhost:8080")
    if err != nil {
        fmt.Printf("地址解析失败: %v\n", err)
        return
    }

    conn, err := net.DialUDP("udp", nil, addr)
    if err != nil {
        fmt.Printf("连接失败: %v\n", err)
        return
    }
    defer conn.Close()

    fmt.Println("UDP客户端启动")

    // 发送数据
    message := "Hello UDP"
    _, err = conn.Write([]byte(message))
    if err != nil {
        fmt.Printf("发送失败: %v\n", err)
        return
    }

    fmt.Printf("已发送: %s\n", message)

    // 接收响应
    buffer := make([]byte, 1024)
    conn.SetReadDeadline(time.Now().Add(5 * time.Second))
    n, _, err := conn.ReadFromUDP(buffer)
    if err != nil {
        fmt.Printf("接收响应失败: %v\n", err)
        return
    }

    fmt.Printf("服务器响应: %s\n", string(buffer[:n]))
}
```

### Python UDP服务器/客户端

```python
# UDP服务器
import socket

def udp_server(host='0.0.0.0', port=8080):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print(f"UDP Server listening on {host}:{port}")

    while True:
        data, addr = sock.recvfrom(1024)
        print(f"Received from {addr}: {data.decode()}")
        # 发送响应
        sock.sendto(b"ACK", addr)

    sock.close()

# UDP客户端
def udp_client(host='localhost', port=8080):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    message = "Hello, Server!"
    sock.sendto(message.encode(), (host, port))
    print(f"Sent: {message}")

    data, server_addr = sock.recvfrom(1024)
    print(f"Received: {data.decode()} from {server_addr}")

    sock.close()
```

### C语言 UDP服务器/客户端

```c
// UDP服务器
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>

#define PORT 8080
#define BUFFER_SIZE 1024

int main() {
    int sock_fd;
    struct sockaddr_in server_addr, client_addr;
    char buffer[BUFFER_SIZE];
    socklen_t len;

    sock_fd = socket(AF_INET, SOCK_DGRAM, 0);

    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);
    bind(sock_fd, (struct sockaddr*)&server_addr, sizeof(server_addr));

    printf("UDP Server listening on port %d\n", PORT);

    while (1) {
        memset(buffer, 0, BUFFER_SIZE);
        len = sizeof(client_addr);
        recvfrom(sock_fd, buffer, BUFFER_SIZE, 0,
                 (struct sockaddr*)&client_addr, &len);
        printf("Received from %s:%d: %s",
               inet_ntoa(client_addr.sin_addr),
               ntohs(client_addr.sin_port), buffer);
        sendto(sock_fd, buffer, strlen(buffer), 0,
               (struct sockaddr*)&client_addr, len);
    }

    close(sock_fd);
    return 0;
}
```

```c
// UDP客户端
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>

#define PORT 8080
#define BUFFER_SIZE 1024

int main() {
    int sock_fd;
    struct sockaddr_in server_addr;
    char buffer[BUFFER_SIZE];

    sock_fd = socket(AF_INET, SOCK_DGRAM, 0);

    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    inet_pton(AF_INET, "127.0.0.1", &server_addr.sin_addr);

    printf("Enter message: ");
    fgets(buffer, BUFFER_SIZE, stdin);
    sendto(sock_fd, buffer, strlen(buffer), 0,
           (struct sockaddr*)&server_addr, sizeof(server_addr));

    memset(buffer, 0, BUFFER_SIZE);
    recvfrom(sock_fd, buffer, BUFFER_SIZE, 0, NULL, NULL);
    printf("Received: %s", buffer);

    close(sock_fd);
    return 0;
}
```

## 常见问题

### 粘包处理

```python
# TCP粘包问题需要自己处理
import struct

class MessageProtocol:
    """TLV (Type-Length-Value) 协议"""

    @staticmethod
    def pack(message: str) -> bytes:
        """打包消息：4字节长度 + 消息内容"""
        data = message.encode('utf-8')
        length = len(data)
        # 打包为4字节无符号大端序整数
        header = struct.pack('!I', length)
        return header + data

    @staticmethod
    def unpack_one(buffer: bytearray) -> tuple[str | None, int]:
        """
        从缓冲区解包一条消息
        返回：(消息内容, 已消耗字节数) 或 (None, 0)
        """
        if len(buffer) < 4:
            return None, 0

        # 读取长度
        length = struct.unpack('!I', bytes(buffer[:4]))[0]

        # 检查是否收到完整消息
        total_len = 4 + length
        if len(buffer) < total_len:
            return None, 0

        # 提取消息
        message = buffer[4:total_len].decode('utf-8')

        # 移除已处理数据
        del buffer[:total_len]

        return message, total_len


def recv_messages(sock):
    """接收完整消息流"""
    buffer = bytearray()
    while True:
        data = sock.recv(4096)
        if not data:
            break
        buffer.extend(data)

        # 循环解包
        while True:
            msg, consumed = MessageProtocol.unpack_one(buffer)
            if consumed == 0:
                break
            yield msg
```

### 心跳机制

```python
import threading
import time

class HeartbeatConnection:
    """带心跳的连接"""

    def __init__(self, conn, interval=30, timeout=90):
        self.conn = conn
        self.interval = interval  # 心跳间隔
        self.timeout = timeout    # 超时时间
        self.last_pong = time.time()
        self.running = True

    def start(self):
        """启动心跳"""
        self.recv_thread = threading.Thread(target=self._heartbeat_check)
        self.recv_thread.daemon = True
        self.recv_thread.start()

    def _heartbeat_check(self):
        """检查心跳是否超时"""
        while self.running:
            if time.time() - self.last_pong > self.timeout:
                print("心跳超时，关闭连接")
                self.conn.close()
                break
            time.sleep(1)

    def send_ping(self):
        """发送心跳"""
        try:
            self.conn.sendall(b"ping")
        except Exception as e:
            print(f"发送心跳失败: {e}")
            self.conn.close()

    def on_pong(self):
        """收到pong"""
        self.last_pong = time.time()
```

## 非阻塞与异步Socket

### 非阻塞Socket

```python
import socket
import select

# 非阻塞服务器
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setblocking(False)  # 非阻塞模式
sock.bind(('0.0.0.0', 8080))
sock.listen(5)

inputs = [sock]
outputs = []

while inputs:
    readable, writable, exceptional = select.select(inputs, outputs, inputs)

    for s in readable:
        if s is sock:
            client, addr = s.accept()
            client.setblocking(False)
            inputs.append(client)
            print(f"Client connected: {addr}")
        else:
            data = s.recv(1024)
            if data:
                print(f"Received: {data}")
                outputs.append(s)
            else:
                inputs.remove(s)
                s.close()
                outputs.remove(s) if s in outputs else None

    for s in writable:
        s.sendall(b"ACK")
        outputs.remove(s)

    for s in exceptional:
        inputs.remove(s)
        outputs.remove(s) if s in outputs else None
        s.close()
```

### 异步Socket (asyncio)

```python
import asyncio

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"Client connected: {addr}")

    while True:
        data = await reader.read(100)
        if not data:
            break
        print(f"Received: {data.decode()}")
        writer.write(data)

    print(f"Client disconnected: {addr}")
    writer.close()
    await writer.wait_closed()

async def main():
    server = await asyncio.start_server(
        handle_client, '0.0.0.0', 8080
    )
    print("Server started on port 8080")
    async with server:
        await server.serve_forever()

asyncio.run(main())
```

## Socket选项

```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 常用Socket选项
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用
sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # TCP保活
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # 禁用Nagle

# 超时设置
sock.settimeout(5.0)  # 5秒超时

# 获取选项
opt_val = sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR)
```

## Socket网络工具

```bash
# 创建简单的TCP测试服务器
nc -l 8080                      # 监听TCP端口 (Linux/Mac)
# Windows: nc -l 8080

# 连接TCP服务器
nc localhost 8080

# UDP测试
nc -u -l 8080                  # 监听UDP端口 (Linux/Mac)
# Windows: nc -u -l 8080
nc -u localhost 8080            # 连接UDP端口

# 端口扫描
nc -zv localhost 8000-9000     # 扫描端口范围

# 传输文件
# 服务器端
nc -l 8080 < file.txt           # Linux/Mac
# 客户端
nc server_ip 8080 > file.txt

# 创建简单的Web服务器
while true; do echo -e "HTTP/1.1 200 OK\r\n\r\n$(date)"; done | nc -l 8080
```

## 常见Socket错误

> **Windows (WSAE\*)** / **Unix (ECONNREFUSED)**
>
> 注意：Unix系统的ECONNREFUSED对应Windows的WSAECONNREFUSED=10061，而非111。

| 错误码 | 平台 | 常量 | 说明 |
|--------|------|------|------|
| 10048 | Windows | WSAEADDRINUSE | 地址已被占用 |
| 10049 | Windows | WSAEADDRNOTAVAIL | 地址不可用 |
| 10053 | Windows | WSAECONNABORTED | 连接被中止 |
| 10054 | Windows | WSAECONNRESET | 连接被重置 |
| 10060 | Windows | WSAETIMEDOUT | 连接超时 |
| 10061 | Windows | WSAECONNREFUSED | 连接被拒绝（Unix的ECONNREFUSED对应此码） |
| 111 | Unix | ECONNREFUSED | 连接被拒绝 |

```python
import errno
import socket

try:
    sock.connect(('localhost', 9999))
except socket.error as e:
    if e.errno == errno.ECONNREFUSED:
        print("Connection refused - server not running")
    elif e.errno == errno.ETIMEDOUT:
        print("Connection timed out")
    else:
        print(f"Socket error: {e}")
```

## 完整示例：多线程聊天服务器

```python
# 多线程TCP聊天服务器
import socket
import threading

class ChatServer:
    def __init__(self, port=8080):
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}  # {addr: socket}

    def start(self):
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(10)
        print(f"Chat server started on port {self.port}")

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Client {addr} connected")
            self.clients[addr] = client_socket
            thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
            thread.daemon = True
            thread.start()

    def handle_client(self, client_socket, addr):
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                message = f"Client {addr}: {data.decode()}"
                print(message)
                self.broadcast(message, addr)
        except Exception as e:
            print(f"Error with client {addr}: {e}")
        finally:
            del self.clients[addr]
            client_socket.close()
            print(f"Client {addr} disconnected")

    def broadcast(self, message, sender_addr):
        for addr, sock in self.clients.items():
            if addr != sender_addr:
                try:
                    sock.sendall(message.encode())
                except:
                    pass

if __name__ == '__main__':
    ChatServer(8080).start()
```

## Socket高性能编程

### 水平触发 vs 边缘触发

```python
# epoll (Linux) - 边缘触发
import selectors

selector = selectors.EpollSelector()
selector.register(sock, selectors.EVENT_READ, data=None)

while True:
    events = selector.select()
    for key, mask in events:
        if mask & selectors.EVENT_READ:
            client, addr = sock.accept()
            selector.register(client, selectors.EVENT_READ)
```

### 常见优化

```python
# 禁用Nagle算法（低延迟）
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

# TCP快速打开 (Linux)
# 需要内核支持: echo 3 > /proc/sys/net/ipv4/tcp_fastopen

# SO_SNDBUF / SO_RCVBUF
sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)

# TCP保活
sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
```

## 网络字节序

```python
import struct

# 字节序转换
byte_order = {
    "主机字节序": "小端（x86）或大端（网络）",
    "网络字节序": "大端序（Big Endian）",
    "原因": "网络协议统一使用大端序"
}

# Python转换函数
def convert_byte_order():
    # 主机序转网络序（大端）
    # 4字节
    network_int = socket.htonl(0x12345678)  # host to network long
    network_short = socket.htons(0x1234)    # host to network short

    # 网络序转主机序
    host_int = socket.ntohl(network_int)    # network to host long
    host_short = socket.ntohs(network_short) # network to host short

    # struct模块也可
    packed = struct.pack('!I', 0x12345678)  # ! 表示网络字节序
    unpacked = struct.unpack('!I', packed)[0]
```
