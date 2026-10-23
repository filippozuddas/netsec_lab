from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json

PORT = 8080
HOST = "0.0.0.0"

notes = {}
next_id = 1

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
            
        elif url.path == "/echo": 
            msg = parse_qs(url.query).get("msg", [""])[0]
            body = json.dumps({"msg": msg}).encode()
            
            self._send(200, body, "application/json")
            
        elif url.path.startswith("/notes/"): 
            id = url.path.split("/")[2]
            if id.isdigit() and int(id) in notes: 
                body = json.dumps({"id": int(id), "text": notes[int(id)]}).encode()
                self._send(200, body, "application/json")
            else: 
                self._send(404)
        
        else: 
            self._send(404)
        
    
    def do_POST(self): 
        global next_id
        url = urlparse(self.path)
        
        if url.path != "/notes": 
            self._send(404)
        elif self.headers.get("Content-Type") != "application/json": 
            self._send(415)
        else: 
            length = int(self.headers.get("Content-Length", 0))
            
            try:
                data = json.loads(self.rfile.read(length))
                text = data["text"]
            except (ValueError, KeyError, TypeError):
                text = None
            if not isinstance(text, str):
                self._send(400)
                return

            notes[next_id] = text

            body = json.dumps({"id": next_id}).encode()
            self._send(201, body, "application/json")
            next_id += 1
            
    def do_DELETE(self): 
        url = urlparse(self.path)
        id = url.path.split("/")[2]
        
        if url.path.startswith("/notes/") and id.isdigit() and int(id) in notes: 
            del notes[int(id)]
            self._send(204)
        else: 
            self._send(404)
            
    def do_PUT(self): 
        if self.path.startswith("/notes"): 
            self._send(405)
        else: 
            self._send(404)
                        
            

if __name__ == "__main__": 
    HTTPServer((HOST, PORT), Handler).serve_forever()
