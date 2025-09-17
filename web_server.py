import ssl
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import os

class WebServer:
    def __init__(self, upload_dir):
        self.upload_dir = upload_dir
        self.httpd = None
        self.server_thread = None

    def start_server(self, port, ip_manager, ssl_enabled=False, certfile=None, keyfile=None):
        os.chdir(self.upload_dir)
        handler = SimpleHTTPRequestHandler
        self.httpd = HTTPServer(('0.0.0.0', port), handler)
        if ssl_enabled and certfile and keyfile:
            self.httpd.socket = ssl.wrap_socket(self.httpd.socket, certfile=certfile, keyfile=keyfile, server_side=True)
        self.server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.server_thread.start()
        return True

    def stop_server(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
