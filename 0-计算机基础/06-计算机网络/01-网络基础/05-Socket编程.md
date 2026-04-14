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

### Python TCP服务器/客户端

```python
# TCP服务器
import socket

def start_server(host='0.0.0.0', port=8080):
    # 创建TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 允许端口复用
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 绑定地址
    server_socket.bind((host, port))
    # 监听连接
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    while True:
        # 接受连接（阻塞）
        client_socket, client_addr = server_socket.accept()
        print(f"Connection from {client_addr}")

        # 处理请求
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                print(f"Received: {data.decode()}")
                # 回显
                client_socket.sendall(data)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            client_socket.close()

    server_socket.close()

# TCP客户端
import socket

def tcp_client(host='localhost', port=8080):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    print(f"Connected to {host}:{port}")

    try:
        message = "Hello, Server!"
        sock.sendall(message.encode())
        print(f"Sent: {message}")

        data = sock.recv(1024)
        print(f"Received: {data.decode()}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()

if __name__ == '__main__':
    start_server()
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

### C++ TCP服务器 (面向对象)

```cpp
// C++ TCP服务器类
#include <iostream>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>

class TCPServer {
private:
    int server_fd;
    int port;
    struct sockaddr_in address;

public:
    TCPServer(int port) : port(port), server_fd(-1) {}

    bool start() {
        server_fd = socket(AF_INET, SOCK_STREAM, 0);
        if (server_fd < 0) return false;

        int opt = 1;
        setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

        address.sin_family = AF_INET;
        address.sin_addr.s_addr = INADDR_ANY;
        address.sin_port = htons(port);

        if (bind(server_fd, (struct sockaddr*)&address, sizeof(address)) < 0) {
            return false;
        }

        if (listen(server_fd, 5) < 0) {
            return false;
        }

        return true;
    }

    int acceptClient(struct sockaddr_in* client_addr) {
        socklen_t len = sizeof(*client_addr);
        return accept(server_fd, (struct sockaddr*)client_addr, &len);
    }

    void close() {
        if (server_fd >= 0) {
            ::close(server_fd);
        }
    }

    ~TCPServer() {
        close();
    }
};

int main() {
    TCPServer server(8080);
    if (!server.start()) {
        std::cerr << "Failed to start server" << std::endl;
        return 1;
    }
    std::cout << "Server started on port 8080" << std::endl;

    struct sockaddr_in client_addr;
    int client_fd = server.acceptClient(&client_addr);
    std::cout << "Client connected" << std::endl;

    // 处理客户端...
    close(client_fd);
    return 0;
}
```

## UDP Socket编程

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
nc -l -p 8080                    # 监听TCP端口
nc -l -p 8080 -c "echo hello"   # 自动回复

# 连接TCP服务器
nc localhost 8080

# UDP测试
nc -u -l -p 8080                # 监听UDP端口
nc -u localhost 8080             # 连接UDP端口

# 端口扫描
nc -zv localhost 8000-9000       # 扫描端口范围

# 传输文件
# 服务器端
nc -l -p 8080 < file.txt
# 客户端
nc server_ip 8080 > file.txt

# 创建简单的Web服务器
while true; do echo -e "HTTP/1.1 200 OK\r\n\r\n$(date)"; done | nc -l -p 8080
```

## 常见Socket错误

| 错误码 | 常量 | 说明 |
|--------|------|------|
| 10048 | WSAEADDRINUSE | 地址已被占用 |
| 10049 | WSAEADDRNOTAVAIL | 地址不可用 |
| 10053 | WSAECONNABORTED | 连接被中止 |
| 10054 | WSAECONNRESET | 连接被重置 |
| 10060 | WSAETIMEDOUT | 连接超时 |
| 111 | ECONNREFUSED | 连接被拒绝 |

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
