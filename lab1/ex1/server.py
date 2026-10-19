from socketserver import BaseRequestHandler, ThreadingTCPServer
import threading

HOST = "0.0.0.0"
PORT = 9001

key_dict = {}
lock = threading.Lock()

class Handler(BaseRequestHandler):
    def handle(self):
        
        buffer = b""
        
        while True:
            msg = self.request.recv(1024)
            
            buffer += msg
            
            if not msg: 
                break
            
            while b"\n" in buffer: 
                command, buffer = buffer.split(b"\n", 1)
                
                if command == b'PING':
                    self.request.sendall(b'PONG\n')

                elif command.startswith(b"ECHO "): 
                    response = command[len(b"ECHO "): ]
                    self.request.sendall(response + b"\n")

                elif command == b"SET" or command.startswith(b"SET "):
                    parts = command.split(b" ", maxsplit=2)

                    if len(parts) < 3 or not parts[1] or not parts[2]: 
                        self.request.sendall(b'ERR\n')
                    else:
                        key = parts[1]
                        value = parts[2]
                        
                        with lock: 
                            key_dict[key] = value
                            
                        self.request.sendall(b'OK\n')

                elif command == b"GET" or command.startswith(b"GET "): 
                    parts = command.split(b" ")

                    if len(parts) != 2 or not parts[1]: 
                        self.request.sendall(b'ERR\n')
                    else: 
                        key = parts[1]
                        
                        with lock: 
                            value = key_dict.get(key)
                        
                        if value is None: 
                            self.request.sendall(b"NOT_FOUND\n")
                        else: 
                            self.request.sendall(value + b"\n")

                else: 
                    self.request.sendall(b'ERR\n')
            

ThreadingTCPServer.allow_reuse_address = True

with ThreadingTCPServer((HOST, PORT), Handler) as server:
    server.serve_forever()