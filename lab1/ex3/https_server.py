from http.server import HTTPSServer, BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from urllib.parse import urlparse
import json
import secrets
import ssl
import threading 

HOST = "0.0.0.0"

sessions = {}

class Handler(BaseHTTPRequestHandler): 
    
    def _send(self, status, body=b"", content_type="text/html"): 
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        
    def do_GET(self): 
        url = urlparse(self.path)
        
        if url.path == "/": 
            self._send(200)
            
        elif url.path == "/me": 
            cookie = SimpleCookie(self.headers.get("Cookie"))
            
            if "session" not in cookie: 
                self._send(401)
                return
            
            user = sessions.get(cookie["session"].value)
            
            if user is None: 
                self._send(401)
                return 
            
            body = json.dumps({"user": user}).encode()
            self._send(200, body, "application/json")
        
        elif url.path == "/whoami":
            cert = self.connection.getpeercert()
            if not cert:
                self._send(401)
                return
            subject = dict(rdn[0] for rdn in cert["subject"])
            self._send(200, subject["commonName"].encode(), "text/plain")
                
            
    def do_POST(self):
        url = urlparse(self.path)
        
        if url.path == "/login": 
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length))
            user, password = data["user"], data["password"]
            
            cookie = SimpleCookie()
            
            if password != "netsec": 
                self._send(401)
                return
             
            token = secrets.token_urlsafe(16)
            sessions[token] = user
            cookie["session"] = token
            cookie["session"]["secure"] = True
            cookie["session"]["httponly"] = True
        
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.send_header('Set-Cookie',cookie["session"].OutputString())
            self.end_headers()
            
if __name__ == "__main__": 
    login_server = HTTPSServer((HOST, 8443), Handler, certfile="server.crt", keyfile="server.key")

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain("server.crt", "server.key")
    context.load_verify_locations("ca.crt")
    context.verify_mode = ssl.CERT_REQUIRED
    
    mtls_server = ThreadingHTTPServer((HOST, 8444), Handler)
    mtls_server.socket = context.wrap_socket(mtls_server.socket, server_side=True)
    
    threading.Thread(target=mtls_server.serve_forever, daemon=True).start()
    login_server.serve_forever()