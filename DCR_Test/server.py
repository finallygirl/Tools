
import socket
import random
import threading

class FloatServer:
    def __init__(self, host='0.0.0.0', port=5025):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server started on {self.host}:{self.port}")
        
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr}")
            client_thread = threading.Thread(
                target=self.handle_client,
                args=(client_socket,)
            )
            client_thread.start()
    
    def handle_client(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                # 无论收到什么命令都返回随机浮点数
                response = str(random.uniform(10000000, 100000000)) + "\n"
                client_socket.sendall(response.encode())
        finally:
            client_socket.close()

if __name__ == "__main__":
    server = FloatServer()
    server.start()
