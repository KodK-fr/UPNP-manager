import socket
import logging

class NetworkScanner:
    @staticmethod
    def get_local_ip():
        """Obtenir l'adresse IP locale."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            logging.error(f"Failed to get local IP: {e}")
            return "127.0.0.1"

    @staticmethod
    def scan_ports(host, start_port, end_port):
        """Scanner les ports ouverts sur un hôte donné."""
        open_ports = []
        for port in range(start_port, end_port + 1):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            result = sock.connect_ex((host, port))
            if result == 0:
                open_ports.append(port)
            sock.close()
        return open_ports

    @staticmethod
    def is_port_available(port):
        """Vérifier si un port est disponible."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('', port))
            sock.close()
            return True
        except:
            return False
