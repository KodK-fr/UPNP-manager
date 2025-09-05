import json
import os

class IPManager:
    def __init__(self, allowed_ips_file='allowed_ips.json', blocked_ips_file='blocked_ips.json'):
        self.allowed_ips_file = allowed_ips_file
        self.blocked_ips_file = blocked_ips_file
        self.allowed_ips = self.load_ips(self.allowed_ips_file)
        self.blocked_ips = self.load_ips(self.blocked_ips_file)

    def load_ips(self, filename):
        """Charger les adresses IP depuis un fichier."""
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_ips(self, filename, ips):
        """Sauvegarder les adresses IP dans un fichier."""
        try:
            with open(filename, 'w') as f:
                json.dump(ips, f)
        except Exception as e:
            print(f"Failed to save IPs: {e}")

    def add_allowed_ip(self, ip):
        """Ajouter une adresse IP autorisée."""
        if ip not in self.allowed_ips:
            self.allowed_ips.append(ip)
            self.save_ips(self.allowed_ips_file, self.allowed_ips)
            return True
        return False

    def remove_allowed_ip(self, ip):
        """Supprimer une adresse IP autorisée."""
        if ip in self.allowed_ips:
            self.allowed_ips.remove(ip)
            self.save_ips(self.allowed_ips_file, self.allowed_ips)
            return True
        return False

    def add_blocked_ip(self, ip):
        """Ajouter une adresse IP bloquée."""
        if ip not in self.blocked_ips:
            self.blocked_ips.append(ip)
            self.save_ips(self.blocked_ips_file, self.blocked_ips)
            return True
        return False

    def remove_blocked_ip(self, ip):
        """Supprimer une adresse IP bloquée."""
        if ip in self.blocked_ips:
            self.blocked_ips.remove(ip)
            self.save_ips(self.blocked_ips_file, self.blocked_ips)
            return True
        return False

    def get_allowed_ips(self):
        """Obtenir la liste des adresses IP autorisées."""
        return self.allowed_ips

    def get_blocked_ips(self):
        """Obtenir la liste des adresses IP bloquées."""
        return self.blocked_ips

    def is_ip_allowed(self, ip):
        """Vérifier si une adresse IP est autorisée."""
        if ip in self.allowed_ips:
            return True
        if ip in self.blocked_ips:
            return False
        return True  # Par défaut, toutes les adresses IP sont autorisées sauf si bloquées
