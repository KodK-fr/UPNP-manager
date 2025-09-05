import os
import threading
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, ip_manager, *args, **kwargs):
        self.ip_manager = ip_manager
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Gérer les requêtes GET avec vérification de l'adresse IP."""
        client_ip = self.client_address[0]
        if not self.ip_manager.is_ip_allowed(client_ip):
            self.send_error(403, "Forbidden: Your IP is not allowed to access this server.")
            return
        super().do_GET()

    def do_POST(self):
        """Gérer les requêtes POST avec vérification de l'adresse IP."""
        client_ip = self.client_address[0]
        if not self.ip_manager.is_ip_allowed(client_ip):
            self.send_error(403, "Forbidden: Your IP is not allowed to access this server.")
            return
        super().do_POST()

class WebServer:
    def __init__(self, upload_dir):
        self.server = None
        self.thread = None
        self.upload_dir = os.path.abspath(upload_dir)

    def start_server(self, port, ip_manager):
        """Démarrer le serveur web avec gestion des adresses IP."""
        try:
            os.chdir(self.upload_dir)
            handler = lambda *args, **kwargs: CustomHTTPRequestHandler(ip_manager, *args, **kwargs)
            self.server = HTTPServer(('', port), handler)
            self.thread = threading.Thread(target=self.server.serve_forever)
            self.thread.daemon = True
            self.thread.start()
            logging.info(f"Server started on port {port}")
            return True
        except Exception as e:
            logging.error(f"Failed to start server: {e}")
            return False

    def stop_server(self):
        """Arrêter le serveur web."""
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
                if self.thread and self.thread.is_alive():
                    self.thread.join(timeout=5)
                logging.info("Server stopped")
                return True
            except Exception as e:
                logging.error(f"Failed to stop server: {e}")
                return False
        return True
